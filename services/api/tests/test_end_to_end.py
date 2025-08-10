from __future__ import annotations

import os
from io import BytesIO
from datetime import date

from fastapi.testclient import TestClient


def _make_jpeg_bytes(width: int = 200, height: int = 120) -> bytes:
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency issue
        raise RuntimeError("Pillow is required for tests") from exc
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def _make_client() -> TestClient:
    # Ensure predictable, test-local config
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_api.db")
    os.environ.setdefault("OCR_PROVIDER", "stub")
    os.environ.setdefault("CORS_ALLOW_ORIGINS", "*")
    # Import after env is set so settings/engine pick them up
    from services.api.app.main import app  # type: ignore

    return TestClient(app)


def test_health_and_readiness():
    client = _make_client()
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    r2 = client.get("/readiness")
    assert r2.status_code == 200
    assert "dependencies" in r2.json()


def test_upload_ocr_autopost_and_reports_flow(tmp_path):
    client = _make_client()

    # 1) Upload document
    img_bytes = _make_jpeg_bytes()
    files = {"file": ("receipt.jpg", img_bytes, "image/jpeg")}
    data = {"meta_json": "{}"}
    up = client.post("/documents", files=files, data=data)
    assert up.status_code == 200, up.text
    doc = up.json()
    doc_id = doc["documentId"]

    # 2) Process OCR (stub)
    ocr = client.post(f"/documents/{doc_id}/process-ocr")
    assert ocr.status_code == 200, ocr.text
    fields = ocr.json().get("fields", [])
    assert isinstance(fields, list) and len(fields) >= 1

    # 2b) Image ETag/304
    img = client.get(f"/documents/{doc_id}/image")
    assert img.status_code == 200
    etag = img.headers.get("ETag")
    assert etag is not None
    img304 = client.get(f"/documents/{doc_id}/image", headers={"If-None-Match": etag})
    assert img304.status_code == 304

    # 3) Auto-post via AI
    today = date.today().isoformat()
    ap = client.post(
        "/ai/auto-post",
        json={
            "org_id": 1,
            "document_id": doc_id,
            "total": 123.45,
            "date": today,
            "vendor": "Kaffe AB",
        },
    )
    assert ap.status_code == 200, ap.text
    ver = ap.json()
    assert "id" in ver and ver["immutable_seq"] >= 1

    # 4) Compliance summary
    cs = client.get(f"/compliance/summary", params={"year": date.today().year})
    assert cs.status_code == 200
    body = cs.json()
    assert "score" in body and "flags" in body

    # 5) Reports (trial balance)
    tb = client.get("/trial-balance", params={"year": date.today().year})
    assert tb.status_code == 200
    tbj = tb.json()
    assert "accounts" in tbj and isinstance(tbj["accounts"], dict)

    # 6) Exports SIE & PDF
    sie = client.get("/exports/sie", params={"year": date.today().year})
    assert sie.status_code == 200
    assert "#SIETYP" in sie.text

    pdf = client.get("/exports/verifications.pdf", params={"year": date.today().year})
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"

    # 7) VAT report JSON
    period = date.today().strftime("%Y-%m")
    vat = client.get("/reports/vat", params={"period": period, "format": "json"})
    assert vat.status_code == 200
    assert "net_vat" in vat.json()

    # 8) Bolagsverket submit (stub)
    bv = client.post("/bolagsverket/submit", json={"year": date.today().year})
    assert bv.status_code == 200
    assert bv.json().get("status") == "queued"


