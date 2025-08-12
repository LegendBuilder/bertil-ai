from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..db import get_session
from ..security import require_user, require_org, enforce_rate_limit
from ..models import BankTransaction, Verification, Entry
from ..matching import suggest_for_transaction
from ..config import settings
from .verifications import VerificationIn, EntryIn, create_verification
from ..camt import parse_camt053


router = APIRouter(prefix="/bank", tags=["bank"])


def _parse_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(text))
    out: list[dict[str, Any]] = []
    for row in reader:
        # Expect columns: date, amount, currency, description, counterparty
        try:
            dt = datetime.fromisoformat(row.get("date", "").split(" ")[0]).date()
            amount = float(str(row.get("amount", "0")).replace(",", "."))
            currency = (row.get("currency") or "SEK").upper()[:3]
            description = (row.get("description") or "").strip()[:500]
            counterparty = (row.get("counterparty") or None)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"bad csv row: {row}") from exc
        out.append({
            "date": dt,
            "amount": amount,
            "currency": currency,
            "description": description,
            "counterparty_ref": counterparty,
        })
    return out


@router.post("/import")
async def import_file(file: UploadFile = File(...), session: AsyncSession = Depends(get_session), user=Depends(require_user), _rl: None = Depends(enforce_rate_limit)) -> dict:
    name = (file.filename or "").lower()
    content = (await file.read())
    rows: list[dict[str, Any]]
    if name.endswith(".csv"):
        rows = _parse_csv(content.decode("utf-8", errors="ignore"))
    elif name.endswith(".xml") or name.endswith(".camt") or name.endswith(".053"):
        try:
            rows = parse_camt053(content.decode("utf-8", errors="ignore"))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="invalid CAMT.053") from exc
    else:
        raise HTTPException(status_code=400, detail="unsupported file type (csv|camt.053)")
    batch_id = int(datetime.utcnow().timestamp())
    for r in rows:
        session.add(BankTransaction(import_batch_id=batch_id, **r))
    await session.commit()
    return {"imported": len(rows), "batch_id": batch_id}


@router.get("/transactions")
async def list_transactions(
    unmatched: int | None = None,
    matched: int | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_user),
    _rl: None = Depends(enforce_rate_limit),
) -> dict:
    stmt = select(BankTransaction)
    # Scope by org if claim present (assumes BankTransaction augmented with org in future)
    conditions = []
    if unmatched:
        conditions.append(BankTransaction.matched_verification_id.is_(None))
    if matched:
        conditions.append(BankTransaction.matched_verification_id.is_not(None))
    if q:
        like = f"%{q}%"
        conditions.append(or_(BankTransaction.description.ilike(like), BankTransaction.counterparty_ref.ilike(like)))
    if date_from:
        try:
            df = datetime.fromisoformat(date_from.split(" ")[0]).date()
            conditions.append(BankTransaction.date >= df)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="invalid date_from") from exc
    if date_to:
        try:
            dt_ = datetime.fromisoformat(date_to.split(" ")[0]).date()
            conditions.append(BankTransaction.date <= dt_)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="invalid date_to") from exc
    if amount_min is not None:
        conditions.append(BankTransaction.amount >= float(amount_min))
    if amount_max is not None:
        conditions.append(BankTransaction.amount <= float(amount_max))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(BankTransaction.id.desc())
    rows = (await session.execute(stmt.offset(offset).limit(limit))).scalars().all()
    return {"items": [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "amount": float(r.amount),
            "currency": r.currency,
            "description": r.description,
            "counterparty": r.counterparty_ref,
            "matched_verification_id": r.matched_verification_id,
        } for r in rows
    ], "limit": limit, "offset": offset}


@router.get("/transactions/{tx_id}/suggest")
async def suggest(tx_id: int, session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    tx = (await session.execute(select(BankTransaction).where(BankTransaction.id == tx_id))).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="not found")
    sugg = await suggest_for_transaction(session, tx)
    return {"items": [{"verification_id": v.id, "immutable_seq": v.immutable_seq, "date": v.date.isoformat(), "total": float(v.total_amount or 0.0), "counterparty": v.counterparty, "score": s} for v, s in sugg]}


@router.post("/transactions/{tx_id}/accept")
async def accept_match(tx_id: int, body: dict, session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    ver_id = int(body.get("verification_id") or 0)
    if ver_id <= 0:
        raise HTTPException(status_code=400, detail="verification_id required")
    tx = (await session.execute(select(BankTransaction).where(BankTransaction.id == tx_id))).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="not found")
    tx.matched_verification_id = ver_id
    await session.commit()
    return {"id": tx.id, "matched_verification_id": ver_id}


@router.post("/transactions/bulk-accept")
async def bulk_accept(body: dict, session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    items = body.get("items") or []
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail="items required")
    updated = 0
    for it in items:
        try:
            tx_id = int(it.get("tx_id"))
            ver_id = int(it.get("verification_id"))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="invalid item") from exc
        tx = (await session.execute(select(BankTransaction).where(BankTransaction.id == tx_id))).scalars().first()
        if not tx:
            continue
        tx.matched_verification_id = ver_id
        updated += 1
    await session.commit()
    return {"updated": updated}


def _compute_open_amount(entries: list[Entry]) -> tuple[str | None, float]:
    """Return (type, amount) where type is 'ar' or 'ap', amount is outstanding > 0 if open.
    Computes based on 1510 (AR) and 2440 (AP) postings.
    """
    sum_1510 = 0.0
    sum_2440 = 0.0
    for e in entries:
        acc = str(e.account)
        debit = float(e.debit or 0.0)
        credit = float(e.credit or 0.0)
        if acc.startswith("1510"):
            sum_1510 += debit - credit
        if acc.startswith("2440"):
            sum_2440 += credit - debit  # payable positive when credit dominates
    if sum_1510 > 0.01:
        return ("ar", round(sum_1510, 2))
    if sum_2440 > 0.01:
        return ("ap", round(sum_2440, 2))
    return (None, 0.0)


@router.post("/transactions/{tx_id}/settle")
async def settle_transaction(tx_id: int, body: dict, session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    ver_id = int(body.get("verification_id") or 0)
    if ver_id <= 0:
        raise HTTPException(status_code=400, detail="verification_id required")
    tx = (await session.execute(select(BankTransaction).where(BankTransaction.id == tx_id))).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="transaction not found")
    v = (await session.execute(select(Verification).where(Verification.id == ver_id))).scalars().first()
    if not v:
        raise HTTPException(status_code=404, detail="verification not found")
    ents = (await session.execute(select(Entry).where(Entry.verification_id == v.id))).scalars().all()
    typ, open_amt = _compute_open_amount(ents)
    if not typ or open_amt <= 0.0:
        raise HTTPException(status_code=400, detail="verification has no open AR/AP amount")
    tx_amt = float(tx.amount)
    # Require sign and magnitude to match (within tolerance)
    if typ == "ar":
        if tx_amt <= 0 or abs(abs(tx_amt) - open_amt) > 0.01:
            raise HTTPException(status_code=400, detail="bank amount does not match AR open amount")
        entries = [
            EntryIn(account=settings.default_settlement_account, debit=open_amt, credit=0.0),
            EntryIn(account="1510", debit=0.0, credit=open_amt),
        ]
    else:  # ap
        if tx_amt >= 0 or abs(abs(tx_amt) - open_amt) > 0.01:
            raise HTTPException(status_code=400, detail="bank amount does not match AP open amount")
        amt = open_amt
        entries = [
            EntryIn(account="2440", debit=amt, credit=0.0),
            EntryIn(account=settings.default_settlement_account, debit=0.0, credit=amt),
        ]
    vin = VerificationIn(
        org_id=v.org_id,
        fiscal_year_id=v.fiscal_year_id,
        date=tx.date,
        total_amount=open_amt,
        currency=v.currency,
        counterparty=v.counterparty,
        document_link=f"/bank/transactions/{tx.id}",
        entries=entries,
    )
    created = await create_verification(vin, session)
    tx.matched_verification_id = int(created.get("id"))
    await session.commit()
    return {"settled_with_verification_id": tx.matched_verification_id}



