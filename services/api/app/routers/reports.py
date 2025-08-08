from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Entry, Verification


router = APIRouter(tags=["reports"])


@router.get("/trial-balance")
async def trial_balance(year: int, session: AsyncSession = Depends(get_session)) -> dict:
    # Aggregate entries for given year: sum(debit) - sum(credit) per account
    rows = (
        await session.execute(
            select(Entry.account, func.sum(Entry.debit), func.sum(Entry.credit))
            .join(Verification, Verification.id == Entry.verification_id)
            .where(func.extract("year", Verification.date) == year)
            .group_by(Entry.account)
            .order_by(Entry.account)
        )
    ).all()
    tb: Dict[str, float] = {}
    for account, sum_debit, sum_credit in rows:
        amount = float(sum_debit or 0.0) - float(sum_credit or 0.0)
        tb[account] = round(amount, 2)
    total = round(sum(tb.values()), 2)
    return {"year": year, "accounts": tb, "total": total}


