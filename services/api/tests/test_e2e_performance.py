import time
from fastapi.testclient import TestClient
from services.api.app.main import app


def test_photo_to_booked_under_5s() -> None:
    with TestClient(app) as client:
        start = time.perf_counter()
        # Upload document
        files = {
            "file": ("kvitto.jpg", b"fake-bytes", "image/jpeg"),
        }
        data = {"meta_json": "{\"org_id\":1,\"type\":\"receipt\"}"}
        r_up = client.post("/documents", files=files, data=data)
        assert r_up.status_code == 200
        doc_id = r_up.json()["documentId"]

        # Process OCR
        r_ocr = client.post(f"/documents/{doc_id}/process-ocr")
        assert r_ocr.status_code == 200
        fields = {f["key"].lower(): f["value"] for f in r_ocr.json().get("fields", [])}
        total = float(fields.get("total", "0").replace(",", "."))
        date_iso = fields.get("date", "2025-01-01")
        vendor = fields.get("vendor", "Okänd")

        # Auto-post
        r_ai = client.post("/ai/auto-post", json={
            "org_id": 1,
            "document_id": doc_id,
            "total": total,
            "date": date_iso,
            "vendor": vendor,
        })
        assert r_ai.status_code == 200
        ver_id = r_ai.json().get("id")
        assert isinstance(ver_id, int)

        elapsed = time.perf_counter() - start
        assert elapsed < 5.0


