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

_attempts: dict[tuple[int, str], int] = {}
_success: dict[tuple[int, str], int] = {}
_blocks: dict[tuple[int, str], int] = {}


def record_attempt(org_id: int, level: str) -> None:
    automation_attempts.labels(org_id=str(org_id), level=level).inc()
    key = (int(org_id), str(level))
    _attempts[key] = _attempts.get(key, 0) + 1
    _update_rate(org_id, level)


def record_success(org_id: int, level: str) -> None:
    automation_success.labels(org_id=str(org_id), level=level).inc()
    key = (int(org_id), str(level))
    _success[key] = _success.get(key, 0) + 1
    _update_rate(org_id, level)


def record_compliance_block(org_id: int, phase: str) -> None:
    compliance_blocked.labels(org_id=str(org_id), phase=phase).inc()
    key = (int(org_id), str(phase))
    _blocks[key] = _blocks.get(key, 0) + 1


def _update_rate(org_id: int, level: str) -> None:
    try:
        att = _attempts.get((int(org_id), str(level)), 0)
        suc = _success.get((int(org_id), str(level)), 0)
        rate = (float(suc) / float(att)) if att > 0 else 0.0
        automation_rate_gauge.labels(org_id=str(org_id), level=str(level)).set(rate)
    except Exception:
        return


def get_kpi_snapshot() -> dict:
    out: dict[str, dict] = {}
    # Build per org summary
    orgs = {org for (org, _lvl) in _attempts.keys()} | {org for (org, _lvl) in _success.keys()}
    for org in sorted(orgs):
        org_map: dict[str, dict] = {}
        for level in ("legacy", "enhanced"):
            att = _attempts.get((org, level), 0)
            suc = _success.get((org, level), 0)
            rate = (float(suc) / float(att)) if att > 0 else 0.0
            org_map[level] = {"attempts": att, "success": suc, "rate": round(rate, 4)}
        pre = _blocks.get((org, "pre"), 0)
        post = _blocks.get((org, "post"), 0)
        org_map["compliance"] = {"pre_blocked": pre, "post_blocked": post}
        out[str(org)] = org_map
    return out


