from __future__ import annotations

from fastapi.testclient import TestClient
from services.api.app.main import app


def test_period_lock_blocks_verification_creation():
    client = TestClient(app)
    # Lock February 2025
    r = client.post("/period/close", json={"org_id": 1, "start_date": "2025-02-01", "end_date": "2025-02-28"})
    assert r.status_code == 200
    # Attempt to create verification inside locked period
    payload = {
        "org_id": 1,
        "date": "2025-02-10",
        "total_amount": 100.0,
        "currency": "SEK",
        "entries": [
            {"account": "1910", "debit": 100.0, "credit": 0.0},
            {"account": "4000", "debit": 0.0, "credit": 100.0},
        ],
    }
    v = client.post("/verifications", json=payload)
    assert v.status_code == 403
    assert "locked" in v.json()["detail"]





