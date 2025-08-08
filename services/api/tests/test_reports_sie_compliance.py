from fastapi.testclient import TestClient
from services.api.app.main import app


def _post_ver(client: TestClient, debit: float, credit: float, counterparty: str = "Kaffe AB", link: str = ".worm_store/aa/bb/" + "a" * 64 + "_kvitto.jpg") -> None:
    payload = {
        "org_id": 1,
        "date": "2025-02-01",
        "total_amount": debit,
        "currency": "SEK",
        "vat_amount": 0.0,
        "counterparty": counterparty,
        "document_link": link,
        "entries": [
            {"account": "1910", "debit": debit, "credit": 0.0},
            {"account": "4000", "debit": 0.0, "credit": credit},
        ],
    }
    r = client.post("/verifications", json=payload)
    assert r.status_code == 200


def test_trial_balance_and_sie_and_compliance() -> None:
    with TestClient(app) as client:
        # Create a balanced verification
        _post_ver(client, 123.0, 123.0)

        # Trial balance
        r_tb = client.get("/trial-balance", params={"year": 2025})
        assert r_tb.status_code == 200
        tb = r_tb.json()
        assert tb["year"] == 2025 and abs(tb["total"]) < 1e-6
        assert "1910" in tb["accounts"] and "4000" in tb["accounts"]

        # SIE export should contain VER and TRANS rows
        r_sie = client.get("/exports/sie", params={"year": 2025})
        assert r_sie.status_code == 200
        content = r_sie.text
        assert "#VER" in content and "#TRANS" in content

        # Compliance summary
        r_comp = client.get("/compliance/summary", params={"year": 2025})
        assert r_comp.status_code == 200
        comp = r_comp.json()
        assert 0 <= comp["score"] <= 100
        assert isinstance(comp["flags"], list)


