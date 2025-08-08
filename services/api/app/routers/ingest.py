from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
import json

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# settings not used in Pass 3 scaffold


router = APIRouter(prefix="/documents", tags=["ingest"])


class DocumentMeta(BaseModel):
    org_id: int
    fiscal_year_id: int | None = None
    type: str = "receipt"
    captured_at: datetime | None = None
    exif: dict[str, Any] | None = None


def _local_worm_store() -> Path:
    root = Path(".worm_store")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _find_document_path(digest: str) -> Path | None:
    store_dir = _local_worm_store() / digest[:2] / digest[2:4]
    if not store_dir.exists():
        return None
    for p in store_dir.iterdir():
        if p.is_file() and p.name.startswith(f"{digest}_"):
            return p
    return None


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    meta_json: str = Form("{}"),
) -> dict:
    # Compute sha256 in a streaming fashion (no full buffering)
    await file.seek(0)
    hasher = hashlib.sha256()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        hasher.update(chunk)
    digest = hasher.hexdigest()
    # Validate client-provided hash if present
    try:
        meta = json.loads(meta_json or "{}")
    except json.JSONDecodeError:
        meta = {}
    client_hash = meta.get("hash_sha256")
    if client_hash and client_hash != digest:
        # Hash mismatch indicates tampering or corruption
        raise HTTPException(status_code=400, detail={"error": "hash_mismatch", "expected": digest, "provided": client_hash})
    store_dir = _local_worm_store() / digest[:2] / digest[2:4]
    store_dir.mkdir(parents=True, exist_ok=True)
    dest = store_dir / f"{digest}_{file.filename}"
    duplicate = dest.exists()
    if not duplicate:
        await file.seek(0)
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    # Return pseudo-id = hash and duplicate flag
    return {"documentId": digest, "storagePath": str(dest), "duplicate": duplicate}


@router.get("/{doc_id}")
async def get_document(doc_id: str) -> dict:
    # Stub OCR/extraction/compliance in Pass 5
    storage_url = f"/documents/{doc_id}/image"
    return {
        "meta": {"id": doc_id, "storageUrl": storage_url},
        "ocr": {
            "text": "stub",
            "boxes": [
                {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.08, "label": "Datum"},
                {"x": 0.1, "y": 0.22, "w": 0.5, "h": 0.1, "label": "Leverantör"},
                {"x": 0.6, "y": 0.8, "w": 0.3, "h": 0.12, "label": "Belopp"},
            ],
        },
        "extracted_fields": [
            {"key": "date", "value": "2025-01-15", "confidence": 0.92},
            {"key": "total", "value": "123.45", "confidence": 0.97},
            {"key": "vendor", "value": "Kaffe AB", "confidence": 0.88},
        ],
        "compliance": {"flags": []},
    }


@router.get("/{doc_id}/image")
async def get_document_image(doc_id: str) -> FileResponse:
    path = _find_document_path(doc_id)
    if path is None or not path.exists():
        # Return 404-like behavior by raising; but for brevity serve empty
        raise FileNotFoundError("document image not found")
    return FileResponse(path)


