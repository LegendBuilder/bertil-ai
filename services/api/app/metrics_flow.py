from __future__ import annotations

from collections import deque
from typing import Deque, List
try:
    from prometheus_client import Histogram  # type: ignore
except Exception:  # pragma: no cover
    class Histogram:  # type: ignore
        def labels(self, *args, **kwargs):
            return self
        def observe(self, *args, **kwargs):
            return None

_flow_latency = Histogram(
    "flow_photo_to_post_seconds",
    "End-to-end latency from photo upload to posting",
    ["flow"],
    # Short buckets for UI responsiveness
    buckets=(0.5, 1, 2, 3, 5, 8, 13, 21),
)

_durations: Deque[float] = deque(maxlen=200)


def record_duration(seconds: float) -> None:
    try:
        if seconds >= 0:
            _durations.append(float(seconds))
            _flow_latency.labels(flow="photo_to_post").observe(float(seconds))
    except Exception:
        pass


def get_stats() -> dict:
    data = list(_durations)
    if not data:
        return {"count": 0, "p95": None, "durations": []}
    data_sorted = sorted(data)
    p95_index = max(0, int(0.95 * (len(data_sorted) - 1)))
    return {"count": len(data_sorted), "p95": round(data_sorted[p95_index], 3), "durations": data_sorted[-20:]}













