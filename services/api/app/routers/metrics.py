from __future__ import annotations

from fastapi import APIRouter
from ..config import settings
import redis.asyncio as redis  # type: ignore
from ..metrics_flow import get_stats
from typing import Optional

router = APIRouter(tags=["metrics"])


@router.get("/metrics/health")
async def metrics_health() -> dict:
    return {"ok": True}


@router.get("/metrics/ocr")
async def metrics_ocr() -> dict:
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
async def metrics_flow() -> dict:
    return get_stats()


_fail_counters: dict[str, int] = {"ocr": 0, "extract": 0, "autopost": 0}


@router.post("/metrics/fail/{area}")
async def record_failure(area: str) -> dict:
    if area not in _fail_counters:
        _fail_counters[area] = 0
    _fail_counters[area] += 1
    return {"area": area, "count": _fail_counters[area]}


@router.get("/metrics/alerts")
async def metrics_alerts() -> dict:
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
    return {"alerts": alerts}


