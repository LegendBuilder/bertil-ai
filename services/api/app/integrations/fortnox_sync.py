from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, date
from typing import Any, Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Document, ExtractedField, BankTransaction


def _make_doc_digest(vendor: str | None, dt_iso: str | None, total: float | None) -> str:
    base = f"{(vendor or '').strip().lower()}|{(dt_iso or '').strip()}|{total or 0.0:.2f}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


async def _sync_receipts(session: AsyncSession, org_id: int, client, access_token: str) -> int:
    count = 0
    items: List[Dict[str, Any]] = await client.list_receipts(access_token)
    for it in items:
        try:
            vendor = (it.get("vendor") or "").strip()
            total = float(it.get("total") or 0.0)
            dt_iso = (it.get("date") or date.today().isoformat())
            digest = _make_doc_digest(vendor, dt_iso, total)
            # Check existing by digest
            existing = (await session.execute(select(Document).where(Document.hash_sha256 == digest))).scalars().first()
            if existing:
                continue
            storage_uri = f"fortnox:receipt:{it.get('id') or digest}"
            doc = Document(
                org_id=org_id,
                fiscal_year_id=None,
                type="receipt",
                storage_uri=storage_uri,
                hash_sha256=digest,
                ocr_text=None,
                status="new",
                created_at=datetime.fromisoformat(f"{dt_iso} 00:00:00"),
            )
            session.add(doc)
            await session.flush()
            # Seed minimal extracted fields
            session.add_all([
                ExtractedField(document_id=doc.id, key="date", value=dt_iso, confidence=0.80),
                ExtractedField(document_id=doc.id, key="total", value=f"{total:.2f}", confidence=0.80),
                ExtractedField(document_id=doc.id, key="vendor", value=vendor, confidence=0.80),
            ])
            count += 1
        except Exception:
            # Skip faulty item, continue
            continue
    await session.commit()
    return count


async def _sync_bank(session: AsyncSession, client, access_token: str) -> int:
    count = 0
    items: List[Dict[str, Any]] = await client.list_bank_transactions(access_token)
    for it in items:
        try:
            dt = datetime.fromisoformat((it.get("date") or str(date.today())))
            amt = float(it.get("amount") or 0.0)
            currency = (it.get("currency") or "SEK").upper()[:3]
            desc = (it.get("description") or "").strip()[:500]
            cp = (it.get("counterparty") or None)
            bt = BankTransaction(
                import_batch_id=int(datetime.utcnow().timestamp()),
                date=dt.date(),
                amount=amt,
                currency=currency,
                description=desc,
                counterparty_ref=cp,
            )
            session.add(bt)
            count += 1
        except Exception:
            continue
    await session.commit()
    return count


async def sync_fortnox(session: AsyncSession, org_id: int, access_token: str, client) -> Dict[str, int]:
    """Fetch receipts and bank transactions from Fortnox with simple retry/backoff.

    Returns {"receipts": N, "bank": M} counts of newly inserted items.
    """
    receipts_count = 0
    bank_count = 0
    # Simple retry: up to 3 attempts with exponential backoff
    for attempt in range(3):
        try:
            receipts_count = await _sync_receipts(session, org_id, client, access_token)
            break
        except Exception:
            await asyncio.sleep(0.25 * (2 ** attempt))
    for attempt in range(3):
        try:
            bank_count = await _sync_bank(session, client, access_token)
            break
        except Exception:
            await asyncio.sleep(0.25 * (2 ** attempt))
    return {"receipts": receipts_count, "bank": bank_count}


