from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge  # type: ignore
except Exception:  # pragma: no cover
    class _Noop:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            return None
        def set(self, *args, **kwargs):
            return None
    def Counter(*args, **kwargs):  # type: ignore
        return _Noop()
    def Gauge(*args, **kwargs):  # type: ignore
        return _Noop()


automation_attempts = Counter(
    "automation_attempts_total",
    "Total auto-post attempts",
    ["org_id", "level"],  # level: enhanced|legacy
)
automation_success = Counter(
    "automation_success_total",
    "Successful auto-post operations",
    ["org_id", "level"],
)
compliance_blocked = Counter(
    "compliance_blocked_total",
    "Pre-check or post-check compliance blocks",
    ["org_id", "phase"],  # phase: pre|post
)
automation_rate_gauge = Gauge(
    "automation_rate",
    "Automation rate calculated as success/attempts",
    ["org_id", "level"],
)


def record_attempt(org_id: int, level: str) -> None:
    automation_attempts.labels(org_id=str(org_id), level=level).inc()
    _update_rate(org_id, level)


def record_success(org_id: int, level: str) -> None:
    automation_success.labels(org_id=str(org_id), level=level).inc()
    _update_rate(org_id, level)


def record_compliance_block(org_id: int, phase: str) -> None:
    compliance_blocked.labels(org_id=str(org_id), phase=phase).inc()


def _update_rate(org_id: int, level: str) -> None:
    try:
        # Compute rate naively from counters if gauges support get, else skip
        # In Prometheus this is usually done with queries; gauge here is best-effort
        # We do not have direct read access; leave as noop (server-side query preferred)
        return
    except Exception:
        return


