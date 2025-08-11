from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import PeriodLock
from ..models import Base


router = APIRouter(prefix="/period", tags=["period"])


@router.get("/status")
async def status(org_id: int = 1, session: AsyncSession = Depends(get_session)) -> dict:
    rows = (
        await session.execute(
            select(PeriodLock).where(PeriodLock.org_id == org_id).order_by(PeriodLock.start_date)
        )
    ).scalars().all()
    return {
        "locked": [
            {"start_date": pl.start_date.isoformat(), "end_date": pl.end_date.isoformat()} for pl in rows
        ]
    }


@router.post("/close")
async def close_period(body: dict, session: AsyncSession = Depends(get_session)) -> dict:
    # Ensure tables exist for local/test SQLite
    try:
        await session.run_sync(lambda conn: Base.metadata.create_all(bind=conn))
    except Exception:
        pass
    try:
        org_id = int(body.get("org_id") or 1)
        start = date.fromisoformat(body["start_date"])  # type: ignore[index]
        end = date.fromisoformat(body["end_date"])  # type: ignore[index]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="invalid payload") from exc
    if end < start:
        raise HTTPException(status_code=400, detail="end_date before start_date")
    pl = PeriodLock(org_id=org_id, start_date=start, end_date=end)
    session.add(pl)
    await session.commit()
    return {"status": "locked", "start_date": start.isoformat(), "end_date": end.isoformat()}





