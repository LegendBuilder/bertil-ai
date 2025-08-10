from __future__ import annotations

from datetime import date
from fastapi.testclient import TestClient
from services.api.app.main import app


def _post_ver(client: TestClient, d: date, debit: float, credit: float, vat_code: str | None = None):
    payload = {
        "org_id": 1,
        "date": d.isoformat(),
        "total_amount": max(debit, credit),
        "currency": "SEK",
        "vat_code": vat_code,
        "entries": [
            {"account": "1910", "debit": debit, "credit": 0.0},
            {"account": "2611", "debit": 0.0, "credit": credit},
        ],
    }
    r = client.post("/verifications", json=payload)
    assert r.status_code == 200


def test_vat_skv_file_export_flagged():
    client = TestClient(app)
    # Post a simple VAT case in 2025-03
    _post_ver(client, date(2025, 3, 5), debit=25.0, credit=25.0, vat_code="SE25")
    # File export is gated; expect 501 until enabled
    r = client.get("/reports/vat/declaration/file", params={"period": "2025-03"})
    assert r.status_code == 501





