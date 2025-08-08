from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, UploadFile
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


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    meta_json: str = Form("{}"),
) -> dict:
    # Compute sha256 while streaming to disk under WORM-like store
    content = await file.read()
    digest = hashlib.sha256(content).hexdigest()
    store_dir = _local_worm_store() / digest[:2] / digest[2:4]
    store_dir.mkdir(parents=True, exist_ok=True)
    dest = store_dir / f"{digest}_{file.filename}"
    if not dest.exists():
        dest.write_bytes(content)
    # Return pseudo-id = hash
    return {"documentId": digest, "storagePath": str(dest)}


@router.get("/{doc_id}")
async def get_document(doc_id: str) -> dict:
    # Stub OCR/extraction/compliance in Pass 2; real in Pass 5
    return {
        "meta": {"id": doc_id},
        "ocr": {"text": "stub"},
        "extracted_fields": [],
        "compliance": {"flags": []},
    }


