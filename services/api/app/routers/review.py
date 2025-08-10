from __future__ import annotations

import json as _json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import ReviewTask


router = APIRouter(prefix="/review", tags=["review"])


@router.get("/inbox")
async def list_tasks(org_id: int = 1, limit: int = 50, session: AsyncSession = Depends(get_session)) -> dict:
    rows = (
        await session.execute(
            select(ReviewTask).where(ReviewTask.org_id == org_id, ReviewTask.status == "pending").order_by(ReviewTask.id)
        )
    ).scalars().all()
    items = [
        {
            "id": r.id,
            "type": r.type,
            "confidence": float(r.confidence or 0.0),
            "payload": _json.loads(r.payload_json or "{}"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows[:limit]
    ]
    return {"items": items}


@router.post("/queue")
async def queue_task(body: dict[str, Any], session: AsyncSession = Depends(get_session)) -> dict:
    org_id = int(body.get("org_id") or 1)
    typ = str(body.get("type") or "generic")
    payload = body.get("payload") or {}
    confidence = float(body.get("confidence") or 0.0)
    rt = ReviewTask(org_id=org_id, type=typ, payload_json=_json.dumps(payload, ensure_ascii=False), confidence=confidence)
    session.add(rt)
    await session.commit()
    return {"id": rt.id}


@router.post("/{task_id}/complete")
async def complete_task(task_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    rt = (await session.execute(select(ReviewTask).where(ReviewTask.id == task_id))).scalars().first()
    if not rt:
        raise HTTPException(status_code=404, detail="not found")
    rt.status = "done"
    await session.commit()
    return {"id": rt.id, "status": rt.status}


@router.post("/{task_id}/reopen")
async def reopen_task(task_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    rt = (await session.execute(select(ReviewTask).where(ReviewTask.id == task_id))).scalars().first()
    if not rt:
        raise HTTPException(status_code=404, detail="not found")
    rt.status = "pending"
    await session.commit()
    return {"id": rt.id, "status": rt.status}


