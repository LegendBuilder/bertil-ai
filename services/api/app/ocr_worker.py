from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict

import redis.asyncio as redis  # type: ignore

from .config import settings
from .ocr import get_ocr_adapter


QUEUE_KEY = "ocr:queue"
RESULTS_KEY = "ocr:results"


async def worker_loop() -> None:
    if not settings.ocr_queue_url:
        raise RuntimeError("OCR queue URL not configured")
    r = redis.from_url(settings.ocr_queue_url, decode_responses=False)
    adapter = get_ocr_adapter()
    import time
    from opentelemetry import trace  # type: ignore
    tracer = trace.get_tracer("bertil.ocr.worker")
    p95_window: list[float] = []
    while True:
        try:
            # BLPOP returns list [key, value]
            item = await r.blpop(QUEUE_KEY, timeout=5)
            if not item:
                await asyncio.sleep(0.1)
                continue
            _key, payload = item
            job = json.loads(payload.decode("utf-8"))
            job_id = job["id"]
            image_bytes = bytes.fromhex(job["hex"])  # image passed as hex
            t0 = time.perf_counter()
            with tracer.start_as_current_span("ocr.job"):
                result = await adapter.extract(image_bytes)
            dt = time.perf_counter() - t0
            p95_window.append(dt)
            if len(p95_window) > 100:
                p95_window.pop(0)
            await r.hset(RESULTS_KEY, job_id, json.dumps({
                "text": result.text,
                "boxes": [asdict(b) for b in result.boxes],
                "extracted_fields": result.extracted_fields,
            }, ensure_ascii=False).encode("utf-8"))
        except Exception:
            await asyncio.sleep(0.5)


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(worker_loop())


