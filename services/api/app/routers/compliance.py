from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_session
from ..compliance import run_yearly_compliance, compute_score

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/summary")
async def compliance_summary(year: int, session: AsyncSession = Depends(get_session)) -> dict:
    flags = await run_yearly_compliance(session, year)
    score = compute_score(flags)
    return {"score": score, "flags": [f.__dict__ for f in flags]}


