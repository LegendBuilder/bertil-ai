from __future__ import annotations

from services.api.app.main import app
from fastapi.testclient import TestClient


def test_einvoice_generate_parse_roundtrip():
    client = TestClient(app)
    payload = {
        "id": "INV-1",
        "issue_date": "2025-01-15",
        "supplier": {"name": "Kaffe AB"},
        "customer": {"name": "Acme"},
        "lines": [
            {"id": "1", "name": "Kaffe", "qty": 1, "price": 100.0},
        ],
    }
    g = client.post("/einvoice/generate", json=payload)
    assert g.status_code == 200
    xml = g.json()["xml"]
    p = client.post("/einvoice/parse", json={"xml": xml})
    assert p.status_code == 200
    inv = p.json()["invoice"]
    assert inv["supplier"]["name"] == "Kaffe AB"














