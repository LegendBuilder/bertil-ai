from fastapi.testclient import TestClient
from services.api.app.main import app


def test_sie_balances_and_sanitizes_accounts() -> None:
    with TestClient(app) as client:
        payload = {
            "org_id": 1,
            "date": "2025-04-01",
            "total_amount": 100.0,
            "currency": "SEK",
            "vat_amount": 0.0,
            "counterparty": "EdgeCase AB",
            "document_link": ".worm_store/aa/bb/{}".format("b" * 64),
            "entries": [
                {"account": "40A0", "debit": 0.0, "credit": 100.0},  # invalid account -> 9999
                {"account": "1910", "debit": 100.0, "credit": 0.0},
            ],
        }
        r = client.post("/verifications", json=payload)
        assert r.status_code == 200
        r_sie = client.get("/exports/sie", params={"year": 2025})
        txt = r_sie.text
        # Ensure #TRANS exists and 9999 present due to account sanitization
        assert "#TRANS 9999" in txt


