from __future__ import annotations

from typing import Any
import os
from fastapi import APIRouter, Depends, HTTPException

from ..config import settings
from ..fortnox_client import get_fortnox_client
from ..security import require_user, require_org
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_session
from ..models import IntegrationToken
from datetime import datetime, timedelta
from ..integrations.fortnox_sync import sync_fortnox


router = APIRouter(prefix="/fortnox", tags=["fortnox"])


@router.get("/oauth/start")
async def oauth_start(user=Depends(require_user)) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    # In real mode, return an authorization URL. For stub, indicate stub flow.
    return {"auth_url": "https://stub.fortnox.local/authorize?client_id=...", "stub": stub}


@router.post("/oauth/callback")
async def oauth_callback(body: dict, user=Depends(require_user), session: AsyncSession = Depends(get_session)) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="code required")
    client = get_fortnox_client(stub)
    tokens = await client.exchange_code(code)
    # Persist tokens to org
    org_id = int(body.get("org_id") or user.get("org_id") or 1)
    try:
        require_org(user, org_id)
    except Exception:
        pass
    expires_in = int(tokens.get("expires_in") or 3600)
    exp_at = datetime.utcnow() + timedelta(seconds=expires_in)
    row = IntegrationToken(org_id=org_id, provider="fortnox", access_token=tokens.get("access_token"), refresh_token=tokens.get("refresh_token"), scope=tokens.get("scope"), expires_at=exp_at)
    session.add(row)
    await session.commit()
    return {"ok": True, "org_id": org_id, "tokens": tokens}


@router.get("/receipts")
async def list_receipts(access_token: str | None = None, org_id: int | None = None, user=Depends(require_user), session: AsyncSession = Depends(get_session)) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    if not access_token and org_id:
        try:
            require_org(user, int(org_id))
        except Exception:
            pass
        row = (await session.execute(select(IntegrationToken).where(IntegrationToken.org_id == int(org_id), IntegrationToken.provider == "fortnox").order_by(IntegrationToken.id.desc()))).scalars().first()
        if not row:
            raise HTTPException(status_code=404, detail="no token for org")
        access_token = row.access_token
    client = get_fortnox_client(stub)
    items = await client.list_receipts(access_token or "stub-token")
    return {"items": items}


@router.get("/bank/transactions")
async def list_bank(access_token: str | None = None, org_id: int | None = None, user=Depends(require_user), session: AsyncSession = Depends(get_session)) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    if not access_token and org_id:
        try:
            require_org(user, int(org_id))
        except Exception:
            pass
        row = (await session.execute(select(IntegrationToken).where(IntegrationToken.org_id == int(org_id), IntegrationToken.provider == "fortnox").order_by(IntegrationToken.id.desc()))).scalars().first()
        if not row:
            raise HTTPException(status_code=404, detail="no token for org")
        access_token = row.access_token
    client = get_fortnox_client(stub)
    items = await client.list_bank_transactions(access_token or "stub-token")
    return {"items": items}


@router.post("/sync")
async def sync(org_id: int, user=Depends(require_user), session: AsyncSession = Depends(get_session)) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    try:
        require_org(user, int(org_id))
    except Exception:
        pass
    row = (await session.execute(select(IntegrationToken).where(IntegrationToken.org_id == int(org_id), IntegrationToken.provider == "fortnox").order_by(IntegrationToken.id.desc()))).scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="no token for org")
    client = get_fortnox_client(stub)
    result = await sync_fortnox(session, int(org_id), row.access_token, client)
    return {"synced": result}





