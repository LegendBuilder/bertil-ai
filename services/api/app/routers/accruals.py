from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from .verifications import VerificationIn, EntryIn, create_verification


router = APIRouter(prefix="/period/accruals", tags=["period"])


class AccrualIn(BaseModel):
    org_id: int = 1
    period: str  # YYYY-MM (apply on last day of period)
    amount: float
    expense_account: str = Field(description="Expense account to accrue, e.g., 4010")
    accrual_account: str = Field(default="2990", description="Balance sheet accrual, default 2990")
    description: Optional[str] = None


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    first_next = date(year, month + 1, 1)
    return first_next - timedelta(days=1)


@router.post("/preview")
async def preview(body: AccrualIn) -> dict:
    y, m = [int(x) for x in body.period.split("-")]
    d_apply = _last_day_of_month(y, m)
    d_reverse = date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
    amt = round(float(body.amount), 2)
    entries_apply = [
        {"account": body.accrual_account, "debit": amt, "credit": 0.0},
        {"account": body.expense_account, "debit": 0.0, "credit": amt},
    ]
    entries_reverse = [
        {"account": body.expense_account, "debit": amt, "credit": 0.0},
        {"account": body.accrual_account, "debit": 0.0, "credit": amt},
    ]
    return {
        "apply_on": d_apply.isoformat(),
        "reverse_on": d_reverse.isoformat(),
        "entries_apply": entries_apply,
        "entries_reverse": entries_reverse,
    }


@router.post("/apply")
async def apply(body: AccrualIn, session: AsyncSession = Depends(get_session)) -> dict:
    prev = await preview(body)
    y, m = [int(x) for x in body.period.split("-")]
    d_apply = date.fromisoformat(prev["apply_on"])  # type: ignore[index]
    d_reverse = date.fromisoformat(prev["reverse_on"])  # type: ignore[index]
    # Create accrual entry on last day
    vin_apply = VerificationIn(
        org_id=body.org_id,
        date=d_apply,
        total_amount=abs(body.amount),
        currency="SEK",
        counterparty=body.description or "Accrual",
        entries=[EntryIn(**e) for e in prev["entries_apply"]],  # type: ignore[arg-type]
    )
    created_apply = await create_verification(vin_apply, session)
    # Create reversing entry on first day next month
    vin_rev = VerificationIn(
        org_id=body.org_id,
        date=d_reverse,
        total_amount=abs(body.amount),
        currency="SEK",
        counterparty=body.description or "Accrual reversal",
        entries=[EntryIn(**e) for e in prev["entries_reverse"]],  # type: ignore[arg-type]
    )
    created_rev = await create_verification(vin_rev, session)
    return {"apply": created_apply, "reverse": created_rev}





