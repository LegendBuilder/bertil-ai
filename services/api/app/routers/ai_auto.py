from __future__ import annotations

from datetime import date
from pathlib import Path
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..security import require_user
from ..ai import suggest_account_and_vat, build_entries, build_entries_with_code
from ..routers.verifications import VerificationIn, EntryIn, create_verification  # reuse model & logic

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/auto-post")
async def auto_post(body: dict[str, Any], session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    # Expecting extracted fields: total, date, vendor
    try:
        total = float(body["total"])  # type: ignore
        dt = date.fromisoformat(body.get("date") or date.today().isoformat())
        vendor = body.get("vendor")
        org_id = int(body.get("org_id") or 1)
        document_id = body.get("document_id")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    decision = await suggest_account_and_vat(vendor, total, session)
    vat_code = body.get("vat_code")
    if vat_code:
        entries = build_entries_with_code(total, decision.expense_account, vat_code)
    else:
        entries = build_entries(total, decision.expense_account, decision.vat_rate)
    vin = VerificationIn(
        org_id=org_id,
        date=dt,
        total_amount=total,
        currency="SEK",
        vat_amount=round(total - (total / (1.0 + decision.vat_rate)), 2) if (not vat_code and decision.vat_rate > 0) else None,
        counterparty=vendor,
        document_link=(f"/documents/{document_id}" if document_id else None),
        vat_code=vat_code,
        entries=[EntryIn(**e) for e in entries],
    )
    # Delegate to existing create_verification route
    created = await create_verification(vin, session)
    explain = f"{decision.reason}. Total {total:.2f} SEK, konto {decision.expense_account}, moms {int(decision.vat_rate*100)}%"
    # Persist explainability in a local sidecar to allow retrieval later
    try:
        meta_dir = Path(".verification_meta")
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / f"{created['id']}.json").write_text(json.dumps({"explainability": explain}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return {**created, "explainability": explain}


