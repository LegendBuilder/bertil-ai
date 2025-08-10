from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_session
from ..compliance import run_yearly_compliance, compute_score, run_verification_rules
from ..models import ComplianceFlag, Verification
from pydantic import BaseModel

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


@router.get("/verification/{ver_id}")
async def verification_flags(ver_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    # Fetch persisted flags
    persisted_stmt = select(ComplianceFlag).where(
        ComplianceFlag.entity_type == "verification", ComplianceFlag.entity_id == ver_id
    )
    persisted = (await session.execute(persisted_stmt)).scalars().all()
    if persisted:
        out = [
            {"rule_code": pf.rule_code, "severity": pf.severity, "message": pf.message}
            for pf in persisted
        ]
        return {"verification_id": ver_id, "flags": out}

    # If none persisted (legacy), compute on the fly
    v = (await session.execute(select(Verification).where(Verification.id == ver_id))).scalars().first()
    if not v:
        return {"verification_id": ver_id, "flags": []}
    computed = await run_verification_rules(session, v)
    return {"verification_id": ver_id, "flags": [f.__dict__ for f in computed]}


class ResolveIn(BaseModel):
    rule_code: str
    actor: str | None = None


@router.post("/verification/{ver_id}/resolve")
async def resolve_flag(ver_id: int, body: ResolveIn, session: AsyncSession = Depends(get_session)) -> dict:
    # Mark matching flags as resolved
    stmt = select(ComplianceFlag).where(
        ComplianceFlag.entity_type == "verification",
        ComplianceFlag.entity_id == ver_id,
        ComplianceFlag.rule_code == body.rule_code,
    )
    flags = (await session.execute(stmt)).scalars().all()
    for f in flags:
        f.resolved_by = body.actor or "user"
    await session.commit()
    return {"verification_id": ver_id, "resolved": body.rule_code, "count": len(flags)}


