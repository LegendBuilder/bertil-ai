from __future__ import annotations

import os
from fastapi.testclient import TestClient
from services.api.app.main import app


def test_fortnox_stub_flow():
    # Enable fortnox in settings
    os.environ["FORTNOX_ENABLED"] = "true"
    os.environ["FORTNOX_STUB"] = "true"
    client = TestClient(app)
    r = client.get("/fortnox/oauth/start")
    assert r.status_code == 200
    cb = client.post("/fortnox/oauth/callback", json={"code": "abc"})
    assert cb.status_code == 200
    token = cb.json()["tokens"]["access_token"]
    rec = client.get("/fortnox/receipts", params={"access_token": token})
    assert rec.status_code == 200
    bank = client.get("/fortnox/bank/transactions", params={"access_token": token})
    assert bank.status_code == 200





