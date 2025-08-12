from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..security import require_user, enforce_rate_limit
from ..sie import parse_sie
from ..routers.verifications import VerificationIn, EntryIn, create_verification


router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/sie")
async def import_sie(file: UploadFile = File(...), session: AsyncSession = Depends(get_session), user=Depends(require_user), _rl: None = Depends(enforce_rate_limit)) -> dict:
    if not file.filename.lower().endswith((".se", ".sie", ".txt")):
        raise HTTPException(status_code=400, detail="expected SIE-like file")
    text = (await file.read()).decode("cp437", errors="ignore")
    parsed = parse_sie(text)
    created = 0
    for v in parsed:
        entries = []
        total = 0.0
        for e in v["entries"]:
            amt = float(e["amount"])  # positive = debit, negative = credit
            if amt >= 0:
                entries.append(EntryIn(account=str(e["account"]), debit=amt, credit=0.0))
            else:
                entries.append(EntryIn(account=str(e["account"]), debit=0.0, credit=-amt))
            total += amt
        if abs(total) > 0.01:
            # balance by adding 9999 line
            if total > 0:
                entries.append(EntryIn(account="9999", debit=0.0, credit=abs(total)))
            else:
                entries.append(EntryIn(account="9999", debit=abs(total), credit=0.0))
        vin = VerificationIn(org_id=1, date=v["date"], total_amount=sum(abs(float(e["amount"])) for e in v["entries"]), currency="SEK", entries=entries)
        await create_verification(vin, session)
        created += 1
    return {"imported": created}













