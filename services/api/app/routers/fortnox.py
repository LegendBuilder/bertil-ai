from __future__ import annotations

from typing import Any
import os
from fastapi import APIRouter, Depends, HTTPException

from ..config import settings
from ..fortnox_client import get_fortnox_client


router = APIRouter(prefix="/fortnox", tags=["fortnox"])


@router.get("/oauth/start")
async def oauth_start() -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    # In real mode, return an authorization URL. For stub, indicate stub flow.
    return {"auth_url": "https://stub.fortnox.local/authorize?client_id=...", "stub": stub}


@router.post("/oauth/callback")
async def oauth_callback(body: dict) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="code required")
    client = get_fortnox_client(stub)
    tokens = await client.exchange_code(code)
    # In production, persist tokens to org/user
    return {"tokens": tokens}


@router.get("/receipts")
async def list_receipts(access_token: str) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    client = get_fortnox_client(stub)
    items = await client.list_receipts(access_token)
    return {"items": items}


@router.get("/bank/transactions")
async def list_bank(access_token: str) -> dict:
    enabled = settings.fortnox_enabled or os.getenv("FORTNOX_ENABLED", "").lower() == "true"
    stub = settings.fortnox_stub or os.getenv("FORTNOX_STUB", "").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=501, detail="fortnox disabled")
    client = get_fortnox_client(stub)
    items = await client.list_bank_transactions(access_token)
    return {"items": items}





