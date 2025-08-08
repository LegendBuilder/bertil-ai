from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..audit import append_audit_event
from ..compliance import run_verification_rules, persist_flags
from ..models import Entry, Verification, AuditLog


router = APIRouter(prefix="/verifications", tags=["ledger"])


class EntryIn(BaseModel):
    account: str
    debit: Optional[float] = 0.0
    credit: Optional[float] = 0.0
    dimension: Optional[str] = None


class VerificationIn(BaseModel):
    org_id: int
    fiscal_year_id: Optional[int] = None
    date: date
    total_amount: float
    currency: str = "SEK"
    vat_amount: Optional[float] = None
    counterparty: Optional[str] = None
    document_link: Optional[str] = None
    entries: List[EntryIn] = Field(default_factory=list)


def _hash_verification_payload(payload: VerificationIn) -> str:
    m = hashlib.sha256()
    m.update(payload.model_dump_json().encode("utf-8"))
    return m.hexdigest()


@router.post("")
async def create_verification(
    body: VerificationIn, session: AsyncSession = Depends(get_session)
) -> dict:
    # Append-only: compute next immutable_seq per org
    next_seq_stmt = select(func.coalesce(func.max(Verification.immutable_seq), 0)).where(
        Verification.org_id == body.org_id
    )
    result = await session.execute(next_seq_stmt)
    next_seq = int(result.scalar_one() or 0) + 1

    v = Verification(
        org_id=body.org_id,
        fiscal_year_id=body.fiscal_year_id,
        immutable_seq=next_seq,
        date=body.date,
        total_amount=body.total_amount,
        currency=body.currency,
        vat_amount=body.vat_amount,
        counterparty=body.counterparty,
        document_link=body.document_link,
        created_at=datetime.utcnow(),
    )
    session.add(v)
    await session.flush()

    # Ensure entries balance (sum debit == sum credit)
    total_debit = 0.0
    total_credit = 0.0
    for e in body.entries:
        total_debit += float(e.debit or 0.0)
        total_credit += float(e.credit or 0.0)
        session.add(
            Entry(
                verification_id=v.id,
                account=e.account,
                debit=e.debit,
                credit=e.credit,
                dimension=e.dimension,
            )
        )
    if round(total_debit - total_credit, 2) != 0.0:
        raise HTTPException(status_code=400, detail="Entries must balance (debit == credit)")

    await session.commit()

    # Hash payload for audit and append to chain
    payload_hash = _hash_verification_payload(body)
    # Use separate tx to ensure verification is persisted before audit record
    async with session.begin():
        chain_hash = await append_audit_event(
            session,
            actor="system",
            action="verification.create",
            target=f"verifications:{v.id}",
            event_payload_hash=payload_hash,
        )
    # Run compliance rules for this verification and persist flags
    flags = await run_verification_rules(session, v)
    if flags:
        await persist_flags(session, "verification", v.id, flags)
    return {"id": v.id, "immutable_seq": v.immutable_seq, "audit_hash": chain_hash}


@router.get("")
async def list_verifications(year: Optional[int] = None, session: AsyncSession = Depends(get_session)) -> list[dict]:
    stmt = select(Verification)
    if year:
        stmt = stmt.where(func.extract("year", Verification.date) == year)
    rows = (await session.execute(stmt.order_by(Verification.id.desc()))).scalars().all()
    return [
        {
            "id": r.id,
            "org_id": r.org_id,
            "immutable_seq": r.immutable_seq,
            "date": r.date.isoformat(),
            "total_amount": float(r.total_amount),
            "currency": r.currency,
        }
        for r in rows
    ]


@router.get("/{ver_id}")
async def get_verification(ver_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    vstmt = select(Verification).where(Verification.id == ver_id)
    v = (await session.execute(vstmt)).scalars().first()
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    estmt = select(Entry).where(Entry.verification_id == v.id)
    entries = (await session.execute(estmt)).scalars().all()
    # Fetch latest audit chain hash for this verification target
    at_stmt = (
        select(AuditLog.after_hash)
        .where(AuditLog.target == f"verifications:{v.id}")
        .order_by(AuditLog.id.desc())
        .limit(1)
    )
    audit_hash = (await session.execute(at_stmt)).scalar_one_or_none()
    # Try load explainability sidecar if exists
    explainability: Optional[str] = None
    try:
        from pathlib import Path
        import json
        meta_path = Path(".verification_meta") / f"{v.id}.json"
        if meta_path.exists():
            explainability = (json.loads(meta_path.read_text(encoding="utf-8")).get("explainability") or None)
    except Exception:
        explainability = None

    return {
        "id": v.id,
        "org_id": v.org_id,
        "immutable_seq": v.immutable_seq,
        "date": v.date.isoformat(),
        "total_amount": float(v.total_amount),
        "currency": v.currency,
        "document_link": v.document_link,
        "entries": [
            {
                "id": e.id,
                "account": e.account,
                "debit": float(e.debit or 0.0),
                "credit": float(e.credit or 0.0),
                "dimension": e.dimension,
            }
            for e in entries
        ],
        "audit_hash": audit_hash,
        "explainability": explainability,
    }


@router.get("/by-document/{doc_id}")
async def get_verification_by_document(doc_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    link = f"/documents/{doc_id}"
    stmt = select(Verification).where(Verification.document_link == link).order_by(Verification.id.desc())
    v = (await session.execute(stmt)).scalars().first()
    if not v:
        return {"id": None, "immutable_seq": None}
    return {"id": v.id, "immutable_seq": v.immutable_seq}


