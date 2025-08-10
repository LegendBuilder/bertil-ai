from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, List, Tuple

from rapidfuzz.fuzz import partial_ratio


@dataclass
class Candidate:
    id: int
    date_ordinal: int
    total_amount: float
    counterparty: str | None


def text_sim(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    try:
        return float(partial_ratio(a.lower(), b.lower())) / 100.0
    except Exception:
        return 0.0


def score_candidate(tx_date_ordinal: int, tx_amount: float, tx_desc: str | None, cand: Candidate, max_days: int = 7) -> float:
    # Amount closeness
    damt = abs(abs(cand.total_amount) - abs(tx_amount))
    denom = max(1.0, abs(cand.total_amount))
    s_amt = max(0.0, 1.0 - (damt / denom))
    # Date proximity
    d = abs(cand.date_ordinal - tx_date_ordinal)
    s_date = max(0.0, 1.0 - (d / float(max_days))) if d <= max_days else 0.0
    # Text similarity
    s_txt = text_sim(tx_desc, cand.counterparty)
    # Weighted
    return 0.6 * s_amt + 0.25 * s_date + 0.15 * s_txt





