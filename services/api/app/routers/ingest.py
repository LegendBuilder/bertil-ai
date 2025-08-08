from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
import json

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from io import BytesIO

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


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_session
from ..models import Document, ExtractedField
from ..ocr import get_ocr_adapter


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    meta_json: str = Form("{}"),
    session: AsyncSession = Depends(get_session),
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
        content_bytes = b""
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                content_bytes += chunk
        # Write simple OCR sidecar stub (length)
        (store_dir / f"{digest}.txt").write_text(f"len:{len(content_bytes)}")
    # Persist Document & extracted fields (stub) if not exists
    doc_stmt = select(Document).where(Document.hash_sha256 == digest)
    existing = (await session.execute(doc_stmt)).scalars().first()
    if existing is None:
        doc = Document(
            org_id=int((meta or {}).get("org_id") or 1),
            fiscal_year_id=None,
            type=str((meta or {}).get("type") or "receipt"),
            storage_uri=str(dest),
            hash_sha256=digest,
            ocr_text=None,
            status="new",
        )
        session.add(doc)
        await session.flush()
        for key, value, conf in (("date", "2025-01-15", 0.92), ("total", "123.45", 0.97), ("vendor", "Kaffe AB", 0.88)):
            session.add(ExtractedField(document_id=doc.id, key=key, value=value, confidence=conf))
        await session.commit()
    # Return pseudo-id = hash and duplicate flag
    return {"documentId": digest, "storagePath": str(dest), "duplicate": duplicate}


@router.get("/{doc_id}")
async def get_document(doc_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    storage_url = f"/documents/{doc_id}/image"
    # Try load from DB
    doc_stmt = select(Document).where(Document.hash_sha256 == doc_id)
    d = (await session.execute(doc_stmt)).scalars().first()
    if d:
        fstmt = select(ExtractedField).where(ExtractedField.document_id == d.id)
        fs = (await session.execute(fstmt)).scalars().all()
        return {
            "meta": {"id": doc_id, "storageUrl": storage_url},
            "ocr": {
                "text": d.ocr_text or "stub-ocr",
                "boxes": [
                    {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.08, "label": "Datum"},
                    {"x": 0.1, "y": 0.22, "w": 0.5, "h": 0.1, "label": "Leverantör"},
                    {"x": 0.6, "y": 0.8, "w": 0.3, "h": 0.12, "label": "Belopp"},
                ],
            },
            "extracted_fields": [
                {"key": f.key, "value": f.value, "confidence": float(f.confidence or 0.0)} for f in fs
            ],
            "compliance": {"flags": []},
        }
    # Deterministic stub values
    return {
        "meta": {"id": doc_id, "storageUrl": storage_url},
        "ocr": {
            "text": "stub-ocr",
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


@router.post("/{doc_id}/process-ocr")
async def process_document_ocr(doc_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    path = _find_document_path(doc_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="document not found")
    adapter = get_ocr_adapter()
    image_bytes = path.read_bytes()
    ocr_result = await adapter.extract(image_bytes)

    # Update DB
    doc_stmt = select(Document).where(Document.hash_sha256 == doc_id)
    d = (await session.execute(doc_stmt)).scalars().first()
    if d is None:
        # Create minimal doc row if missing (idempotent behavior)
        d = Document(
            org_id=1,
            fiscal_year_id=None,
            type="receipt",
            storage_uri=str(path),
            hash_sha256=doc_id,
            ocr_text=ocr_result.text,
            status="ocr_processed",
        )
        session.add(d)
        await session.flush()
    else:
        d.ocr_text = ocr_result.text
        d.status = "ocr_processed"

    # Replace extracted fields
    # Simpler: delete existing then insert (SQLite-friendly)
    await session.execute(
        ExtractedField.__table__.delete().where(ExtractedField.document_id == d.id)
    )
    for key, value, conf in ocr_result.extracted_fields:
        session.add(ExtractedField(document_id=d.id, key=key, value=str(value), confidence=float(conf)))
    await session.commit()

    # Sidecar JSON
    sidecar = path.parent / f"{path.stem}.ocr.json"
    sidecar.write_text(ocr_result.to_json(), encoding="utf-8")

    return {
        "status": "processed",
        "documentId": doc_id,
        "fields": [{"key": k, "value": v, "confidence": conf} for k, v, conf in ocr_result.extracted_fields],
    }

