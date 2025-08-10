from __future__ import annotations

from collections import deque
from typing import Deque, List

_durations: Deque[float] = deque(maxlen=200)


def record_duration(seconds: float) -> None:
    try:
        if seconds >= 0:
            _durations.append(float(seconds))
    except Exception:
        pass


def get_stats() -> dict:
    data = list(_durations)
    if not data:
        return {"count": 0, "p95": None, "durations": []}
    data_sorted = sorted(data)
    p95_index = max(0, int(0.95 * (len(data_sorted) - 1)))
    return {"count": len(data_sorted), "p95": round(data_sorted[p95_index], 3), "durations": data_sorted[-20:]}








