from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..ai import suggest_account_and_vat, build_entries
from ..routers.verifications import VerificationIn, EntryIn, create_verification  # reuse model & logic

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/auto-post")
async def auto_post(body: dict[str, Any], session: AsyncSession = Depends(get_session)) -> dict:
    # Expecting extracted fields: total, date, vendor
    try:
        total = float(body["total"])  # type: ignore
        dt = date.fromisoformat(body.get("date") or date.today().isoformat())
        vendor = body.get("vendor")
        org_id = int(body.get("org_id") or 1)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    decision = suggest_account_and_vat(vendor, total)
    entries = build_entries(total, decision.expense_account, decision.vat_rate)
    vin = VerificationIn(
        org_id=org_id,
        date=dt,
        total_amount=total,
        currency="SEK",
        vat_amount=None,
        counterparty=vendor,
        document_link=None,
        entries=[EntryIn(**e) for e in entries],
    )
    # Delegate to existing create_verification route
    created = await create_verification(vin, session)
    return {
        **created,
        "explainability": f"{decision.reason}. Total {total:.2f} SEK, konto {decision.expense_account}, moms {int(decision.vat_rate*100)}%",
    }


