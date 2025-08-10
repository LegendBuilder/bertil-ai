from __future__ import annotations

from fastapi.testclient import TestClient
from services.api.app.main import app


def test_accrual_preview_and_apply():
    client = TestClient(app)
    prev = client.post("/period/accruals/preview", json={
        "org_id": 1,
        "period": "2025-04",
        "amount": 1200.0,
        "expense_account": "4010",
        "accrual_account": "2990",
        "description": "April accrual",
    })
    assert prev.status_code == 200
    body = prev.json()
    assert body["apply_on"].endswith("-30")
    app_res = client.post("/period/accruals/apply", json={
        "org_id": 1,
        "period": "2025-04",
        "amount": 1200.0,
        "expense_account": "4010",
        "accrual_account": "2990",
        "description": "April accrual",
    })
    assert app_res.status_code == 200
    data = app_res.json()
    assert "apply" in data and "reverse" in data





