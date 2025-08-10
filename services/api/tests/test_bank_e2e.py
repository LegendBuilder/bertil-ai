from __future__ import annotations

from io import BytesIO
from fastapi.testclient import TestClient
from services.api.app.main import app


def test_bank_end_to_end_clear_sample_lines():
    client = TestClient(app)
    # Import simple CSV with two lines
    csv_data = (
        "date,amount,currency,description,counterparty\n"
        "2025-03-01,100.00,SEK,Card Kaffe AB,Kaffe AB\n"
        "2025-03-02,-50.00,SEK,Refund Station,OKQ8\n"
    ).encode("utf-8")
    files = {"file": ("bank.csv", BytesIO(csv_data), "text/csv")}
    r = client.post("/bank/import", files=files)
    assert r.status_code == 200
    # Create verifications that the matcher should find
    v1 = client.post("/verifications", json={
        "org_id": 1,
        "date": "2025-03-01",
        "total_amount": 100.0,
        "currency": "SEK",
        "counterparty": "Kaffe AB",
        "entries": [
            {"account": "5811", "debit": 100.0, "credit": 0.0},
            {"account": "1930", "debit": 0.0, "credit": 100.0},
        ],
    })
    assert v1.status_code == 200
    v2 = client.post("/verifications", json={
        "org_id": 1,
        "date": "2025-03-02",
        "total_amount": 50.0,
        "currency": "SEK",
        "counterparty": "OKQ8",
        "entries": [
            {"account": "1930", "debit": 50.0, "credit": 0.0},
            {"account": "4010", "debit": 0.0, "credit": 50.0},
        ],
    })
    assert v2.status_code == 200
    # Get unmatched and suggest
    lst = client.get("/bank/transactions", params={"unmatched": 1})
    assert lst.status_code == 200
    items = lst.json()["items"]
    cleared = 0
    for it in items:
        tx_id = it["id"]
        sug = client.get(f"/bank/transactions/{tx_id}/suggest").json()["items"]
        if sug:
            acc = client.post(f"/bank/transactions/{tx_id}/accept", json={"verification_id": sug[0]["verification_id"]})
            assert acc.status_code == 200
            cleared += 1
    assert cleared >= 1





