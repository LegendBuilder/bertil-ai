from __future__ import annotations

import math
import re
from datetime import timedelta
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .models import Verification, BankTransaction
from .ml.matcher import Candidate, score_candidate


def _normalize(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _sim(a: str, b: str) -> float:
    # Simple token overlap similarity
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union


async def suggest_for_transaction(session: AsyncSession, tx: BankTransaction, *, max_days: int = 7, max_results: int = 5) -> List[Tuple[Verification, float]]:
    # Fetch recent verifications near date and amount magnitude
    lo = tx.date - timedelta(days=max_days)
    hi = tx.date + timedelta(days=max_days)
    stmt = (
        select(Verification)
        .where(Verification.date.between(lo, hi))
        .order_by(Verification.id.desc())
        .limit(200)
    )
    cands = (await session.execute(stmt)).scalars().all()

    out: List[Tuple[Verification, float]] = []
    tx_do = tx.date.toordinal()
    tx_amt = float(tx.amount)
    for v in cands:
        cand = Candidate(
            id=v.id,
            date_ordinal=v.date.toordinal(),
            total_amount=float(v.total_amount or 0.0),
            counterparty=v.counterparty,
        )
        score = score_candidate(tx_do, tx_amt, tx.description, cand, max_days=max_days)
        if score > 0.2:
            out.append((v, score))
    out.sort(key=lambda x: x[1], reverse=True)
    return out[:max_results]



