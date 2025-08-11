from __future__ import annotations

import argparse
import asyncio
import os
import random
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Optional


def make_image_bytes() -> bytes:
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Pillow required") from exc
    img = Image.new("RGB", (400, 260), color=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def run_httpx(base_url: str, loops: int) -> None:
    import httpx  # type: ignore

    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        for _ in range(loops):
            files = {"file": ("test.jpg", make_image_bytes(), "image/jpeg")}
            data = {"meta_json": "{}"}
            r = await client.post("/documents", files=files, data=data)
            r.raise_for_status()
            doc_id = r.json()["documentId"]
            r2 = await client.post(f"/documents/{doc_id}/process-ocr")
            r2.raise_for_status()
            # autopost
            await client.post(
                "/ai/auto-post",
                json={"org_id": 1, "document_id": doc_id, "total": 123.45, "date": "2025-01-15", "vendor": "Kaffe AB"},
            )


async def run_testclient(loops: int) -> None:
    from fastapi.testclient import TestClient  # type: ignore
    from services.api.app.main import app

    client = TestClient(app)
    for _ in range(loops):
        files = {"file": ("test.jpg", make_image_bytes(), "image/jpeg")}
        data = {"meta_json": "{}"}
        up = client.post("/documents", files=files, data=data)
        up.raise_for_status()
        doc_id = up.json()["documentId"]
        ocr = client.post(f"/documents/{doc_id}/process-ocr")
        ocr.raise_for_status()
        client.post("/ai/auto-post", json={"org_id": 1, "document_id": doc_id, "total": 123.45, "date": "2025-01-15", "vendor": "Kaffe AB"})


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--mode", choices=["httpx", "testclient"], default="testclient")
    parser.add_argument("--budget", type=float, default=None, help="Max average seconds per flow; fail if exceeded")
    args = parser.parse_args()

    per_worker = max(1, args.requests // args.concurrency)
    t0 = time.perf_counter()
    if args.mode == "httpx":
        await asyncio.gather(*[run_httpx(args.base_url, per_worker) for _ in range(args.concurrency)])
    else:
        await asyncio.gather(*[run_testclient(per_worker) for _ in range(args.concurrency)])
    dt = time.perf_counter() - t0
    avg = dt/(per_worker*args.concurrency)
    print(f"Completed {per_worker*args.concurrency} flows in {dt:.2f}s (avg {avg:.3f}s)")
    if args.budget is not None and avg > args.budget:
        raise SystemExit(2)


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())



