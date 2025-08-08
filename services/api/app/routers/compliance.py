from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_session
from ..compliance import run_yearly_compliance, compute_score
from ..models import ComplianceFlag

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/summary")
async def compliance_summary(year: int, session: AsyncSession = Depends(get_session)) -> dict:
    flags = await run_yearly_compliance(session, year)
    score = compute_score(flags)
    persisted_stmt = select(ComplianceFlag)
    persisted = (await session.execute(persisted_stmt)).scalars().all()
    persisted_out = [
        {"rule_code": pf.rule_code, "severity": pf.severity, "message": pf.message}
        for pf in persisted
    ]
    return {"year": year, "score": score, "flags": [f.__dict__ for f in flags] + persisted_out}


