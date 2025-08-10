from __future__ import annotations

from io import BytesIO
from datetime import date

from fastapi.testclient import TestClient
from services.api.app.main import app


def _create_ar_verification(client: TestClient, amount: float) -> int:
    payload = {
        "org_id": 1,
        "date": date.today().isoformat(),
        "total_amount": amount,
        "currency": "SEK",
        "counterparty": "Kund AB",
        "entries": [
            {"account": "1510", "debit": amount, "credit": 0.0},
            {"account": "3001", "debit": 0.0, "credit": amount},
        ],
    }
    r = client.post("/verifications", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _import_bank_tx(client: TestClient, amount: float) -> int:
    csv_data = (
        "date,amount,currency,description,counterparty\n"
        f"{date.today().isoformat()},{amount:.2f},SEK,Inbetalning Kund AB,Kund AB\n"
    ).encode("utf-8")
    files = {"file": ("bank.csv", BytesIO(csv_data), "text/csv")}
    r = client.post("/bank/import", files=files)
    assert r.status_code == 200
    lst = client.get("/bank/transactions", params={"unmatched": 1})
    assert lst.status_code == 200
    items = lst.json()["items"]
    assert items, "no bank transactions after import"
    return items[0]["id"]


def test_settle_ar_against_bank():
    client = TestClient(app)
    amount = 1000.00
    ver_id = _create_ar_verification(client, amount)
    tx_id = _import_bank_tx(client, amount)
    r = client.post(f"/bank/transactions/{tx_id}/settle", json={"verification_id": ver_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("settled_with_verification_id") is not None





