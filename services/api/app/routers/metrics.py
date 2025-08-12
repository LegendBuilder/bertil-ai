from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, Depends
from ..config import settings
from ..security import get_rate_limit_block_count
from ..security import require_user
import redis.asyncio as redis  # type: ignore
from ..metrics_flow import get_stats
from ..metrics_kpis import get_kpi_snapshot
from typing import Optional

router = APIRouter(tags=["metrics"])


@router.get("/metrics/health")
async def metrics_health() -> dict:
    return {"ok": True}


@router.get("/metrics/ocr")
async def metrics_ocr(user=Depends(require_user)) -> dict:
    depth = None
    if settings.ocr_queue_url:
        try:
            r = redis.from_url(settings.ocr_queue_url, decode_responses=False)
            depth = int(await r.llen("ocr:queue"))
        except Exception:
            depth = -1
    warn = bool(depth is not None and depth >= settings.ocr_queue_warn_threshold)
    return {"queue_depth": depth, "provider": settings.ocr_provider, "queued": bool(settings.ocr_queue_url), "warn": warn}


@router.get("/metrics/flow")
async def metrics_flow(user=Depends(require_user)) -> dict:
    return get_stats()


_fail_counters: dict[str, int] = {"ocr": 0, "extract": 0, "autopost": 0}
_frontend_events: dict[str, int] = {}


@router.post("/metrics/fail/{area}")
async def record_failure(area: str, user=Depends(require_user)) -> dict:
    if area not in _fail_counters:
        _fail_counters[area] = 0
    _fail_counters[area] += 1
    return {"area": area, "count": _fail_counters[area]}


@router.get("/metrics/alerts")
async def metrics_alerts(user=Depends(require_user)) -> dict:
    alerts = []
    # OCR queue depth alert
    try:
        depth = None
        if settings.ocr_queue_url:
            r = redis.from_url(settings.ocr_queue_url, decode_responses=False)
            depth = int(await r.llen("ocr:queue"))
        if depth is not None and depth >= settings.ocr_queue_warn_threshold:
            alerts.append({"type": "ocr_queue", "level": "warning", "message": f"OCR queue depth {depth}"})
    except Exception:
        alerts.append({"type": "ocr_queue", "level": "error", "message": "Failed to read OCR queue"})
    # Failure counters
    for k, v in _fail_counters.items():
        if v > 0:
            alerts.append({"type": f"{k}_failures", "level": "warning", "message": f"{v} failures in {k}"})
    # Rate limit blocks
    rl_blocks = get_rate_limit_block_count()
    if rl_blocks > 0:
        alerts.append({"type": "rate_limit", "level": "warning", "message": f"{rl_blocks} requests blocked by rate limiter"})
    return {"alerts": alerts}


@router.get("/metrics/kpi")
async def metrics_kpi(user=Depends(require_user)) -> dict:
    return get_kpi_snapshot()


@router.post("/metrics/event")
async def metrics_event(payload: dict, user=Depends(require_user)) -> dict:
    """Accept lightweight frontend analytics events without PII.

    Payload: {"name": str, "params": dict, "platform": "web"|"mobile"}
    We only count by name to keep this extremely privacy-preserving.
    """
    name = (payload.get("name") or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail={"error": "missing_name"})
    _frontend_events[name] = _frontend_events.get(name, 0) + 1
    return {"ok": True, "name": name, "count": _frontend_events[name]}


@router.get("/metrics/event/stats")
async def metrics_event_stats(user=Depends(require_user)) -> dict:
    return {"events": _frontend_events}


@router.get("/metrics")
async def metrics_prometheus() -> Response:
    """Expose Prometheus metrics in text format.

    Falls back gracefully when prometheus_client is not installed.
    """
    try:  # Lazy import to avoid hard dependency during tests without extras
        from prometheus_client import generate_latest, REGISTRY  # type: ignore
        data = generate_latest(REGISTRY)
        return Response(content=data, media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception:
        # Minimal fallback to ensure endpoint exists in environments without prometheus_client
        return Response(content="# metrics unavailable", media_type="text/plain")


@router.get("/metrics/synthetic")
async def synthetic_health(user=Depends(require_user)) -> dict:
    """Synthetic healthcheck combining OCR queue, flow latency, and rate limits."""
    flow = get_stats()
    alerts = []
    try:
        depth = None
        if settings.ocr_queue_url:
            r = redis.from_url(settings.ocr_queue_url, decode_responses=False)
            depth = int(await r.llen("ocr:queue"))
        if depth is not None and depth >= settings.ocr_queue_warn_threshold:
            alerts.append({"type": "ocr_queue", "level": "warning", "message": f"depth={depth}"})
    except Exception:
        alerts.append({"type": "ocr_queue", "level": "error", "message": "probe-failed"})
    rl_blocks = get_rate_limit_block_count()
    if rl_blocks > 0:
        alerts.append({"type": "rate_limit", "level": "warning", "message": str(rl_blocks)})
    status = "ok"
    if flow.get("p95") and float(flow.get("p95") or 0.0) > 13:
        status = "degraded"
    if any(a.get("level") == "error" for a in alerts):
        status = "error"
    return {"status": status, "flow": flow, "alerts": alerts}


