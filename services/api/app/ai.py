from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from sqlalchemy import select

from .vendor_embeddings import embed_vendor_name
from sqlalchemy.ext.asyncio import AsyncSession
from .models import VendorEmbedding

# Feedback-aware mapping: prefer explicit user feedback over embeddings/heuristics
async def _lookup_feedback(session: AsyncSession, vendor: str | None) -> MappingDecision | None:
    if not session or not vendor:
        return None
    try:
        from .models_feedback import AiFeedback  # lazy import to avoid circular in tests without migration
    except Exception:
        return None
    try:
        stmt = select(AiFeedback).where(AiFeedback.vendor_ilike == vendor.lower()).order_by(AiFeedback.id.desc())
        row = (await session.execute(stmt)).scalars().first()
        if row and (row.correct_account or row.correct_vat_code or row.correct_vat_rate is not None):
            account = row.correct_account or None
            # VAT precedence: explicit code -> rate
            if row.correct_vat_code:
                # Map common codes to rate when building entries is not code-based
                code = row.correct_vat_code.upper()
                if code == "SE12":
                    rate = 0.12
                elif code == "SE06":
                    rate = 0.06
                else:
                    rate = 0.25
            else:
                rate = float(row.correct_vat_rate) if row.correct_vat_rate is not None else 0.25
            if account is None:
                # keep default heuristic account if not set; indicate reason
                return None
            return MappingDecision(account, rate, "Användarfeedback prioriterad")
    except Exception:
        return None
    return None

@dataclass
class MappingDecision:
    expense_account: str
    vat_rate: float  # 0.0..1.0
    reason: str


async def _lookup_vendor_embedding(session: AsyncSession, vendor: str) -> MappingDecision | None:
    vec = embed_vendor_name(vendor)
    # Simple nearest neighbor (cosine via dot product assuming normalized embeddings)
    # If pgvector is available we could use <-> operator; here we fetch small set
    rows = (await session.execute(select(VendorEmbedding))).scalars().all()
    best = None
    best_score = -1.0
    for r in rows:
        if isinstance(r.embedding, (list, tuple)):
            emb = list(map(float, r.embedding))
        else:
            try:
                emb = [float(x) for x in str(r.embedding).split(',')]
            except Exception:
                continue
        score = sum(a*b for a, b in zip(vec, emb))
        if score > best_score:
            best_score = score
            best = r
    if best and best.suggested_account and best.vat_rate is not None:
        return MappingDecision(best.suggested_account, float(best.vat_rate), f"Embeddings träff ({best.name})")
    return None


async def suggest_account_and_vat(vendor: str | None, total_amount: float, session: AsyncSession | None = None) -> MappingDecision:
    v = (vendor or "").lower()
    # 0) Use prior feedback first if available
    if session is not None and vendor:
        fb = await _lookup_feedback(session, vendor)
        if fb:
            return fb
    # Embedding-based suggestion when session provided and we have a dictionary
    if session is not None and vendor:
        hit = await _lookup_vendor_embedding(session, vendor)
        if hit:
            return hit
    if any(k in v for k in ["kaffe", "café", "cafe", "fika", "lunch"]):
        return MappingDecision("5811", 0.12, "Leverantör antyder representation (12% moms)")
    if "taxi" in v:
        return MappingDecision("5611", 0.06, "Taxi-resor (6% moms)")
    if any(k in v for k in ["shell", "circle k", "preem", "okq8"]):
        return MappingDecision("5611", 0.25, "Drivmedel (25% moms)")
    return MappingDecision("4000", 0.25, "Standard inköp (25% moms)")


def build_entries(total_amount: float, expense_account: str, vat_rate: float) -> list[dict]:
    if vat_rate <= 0:
        return [
            {"account": expense_account, "debit": round(total_amount, 2), "credit": 0.0},
            {"account": "1910", "debit": 0.0, "credit": round(total_amount, 2)},
        ]
    net = round(total_amount / (1.0 + vat_rate), 2)
    vat = round(total_amount - net, 2)
    return [
        {"account": expense_account, "debit": net, "credit": 0.0},
        {"account": "2641", "debit": vat, "credit": 0.0},
        {"account": "1910", "debit": 0.0, "credit": round(total_amount, 2)},
    ]


def build_entries_with_code(total_amount: float, expense_account: str, vat_code: str | None) -> list[dict]:
    """Build entries based on a VAT code. Supports:
    - SE25/SE12/SE06: normal purchase with ingående moms on 2641
    - RC25 / EU-RC-SERV: reverse charge (credit 2615, debit 2645) on base = total_amount
    Fallback to 25% if missing/unknown.
    """
    code = (vat_code or "SE25").upper()
    if code.startswith("RC") or code.startswith("EU-RC"):
        rate = 0.25
        base = round(total_amount, 2)
        vat = round(base * rate, 2)
        return [
            {"account": expense_account, "debit": base, "credit": 0.0},
            {"account": "2615", "debit": 0.0, "credit": vat},
            {"account": "2645", "debit": vat, "credit": 0.0},
            {"account": "1910", "debit": 0.0, "credit": base},
        ]
    rate = 0.25
    if code == "SE12":
        rate = 0.12
    elif code == "SE06":
        rate = 0.06
    return build_entries(total_amount, expense_account, rate)

