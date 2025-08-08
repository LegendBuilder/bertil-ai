from fastapi.testclient import TestClient
from services.api.app.main import app


def test_create_balanced_verification() -> None:
    with TestClient(app) as client:
        payload = {
            "org_id": 1,
            "date": "2024-12-31",
            "total_amount": 100.0,
            "currency": "SEK",
            "entries": [
                {"account": "1910", "debit": 100.0, "credit": 0.0},
                {"account": "3001", "debit": 0.0, "credit": 100.0},
            ],
        }
        r = client.post("/verifications", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "id" in data and isinstance(data["immutable_seq"], int) and data["immutable_seq"] >= 1


def test_get_verification_by_document() -> None:
    with TestClient(app) as client:
        doc_id = "c" * 64
        payload = {
            "org_id": 1,
            "date": "2025-02-02",
            "total_amount": 50.0,
            "currency": "SEK",
            "vat_amount": 0.0,
            "counterparty": "DocLink AB",
            "document_link": f"/documents/{doc_id}",
            "entries": [
                {"account": "1910", "debit": 50.0, "credit": 0.0},
                {"account": "4000", "debit": 0.0, "credit": 50.0},
            ],
        }
        r = client.post("/verifications", json=payload)
        assert r.status_code == 200
        r2 = client.get(f"/verifications/by-document/{doc_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert isinstance(data.get("id"), int)


def test_unbalanced_verification_rejected() -> None:
    with TestClient(app) as client:
        payload = {
            "org_id": 1,
            "date": "2025-01-01",
            "total_amount": 100.0,
            "currency": "SEK",
            "entries": [
                {"account": "1910", "debit": 90.0, "credit": 0.0},
                {"account": "3001", "debit": 0.0, "credit": 100.0},
            ],
        }
        r = client.post("/verifications", json=payload)
        assert r.status_code == 400
        assert "balance" in r.json()["detail"]


