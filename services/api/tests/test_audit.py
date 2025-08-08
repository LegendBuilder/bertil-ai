from fastapi.testclient import TestClient
from services.api.app.main import app


def test_audit_chain_updates() -> None:
    with TestClient(app) as client:
        payload = {
            "org_id": 1,
            "date": "2025-01-15",
            "total_amount": 50.0,
            "currency": "SEK",
            "entries": [
                {"account": "1910", "debit": 50.0, "credit": 0.0},
                {"account": "4000", "debit": 0.0, "credit": 50.0},
            ],
        }
        r1 = client.post("/verifications", json=payload)
        assert r1.status_code == 200
        h1 = r1.json()["audit_hash"]

        r2 = client.post("/verifications", json=payload)
        assert r2.status_code == 200
        h2 = r2.json()["audit_hash"]

        assert h1 != h2  # chain extends and changes


