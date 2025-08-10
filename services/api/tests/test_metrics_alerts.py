from __future__ import annotations

from fastapi.testclient import TestClient
from services.api.app.main import app


def test_metrics_alerts_and_fail_counter():
    client = TestClient(app)
    # Record failures
    r1 = client.post("/metrics/fail/ocr")
    assert r1.status_code == 200
    r2 = client.post("/metrics/fail/autopost")
    assert r2.status_code == 200
    alerts = client.get("/metrics/alerts")
    assert alerts.status_code == 200
    body = alerts.json()
    assert isinstance(body.get("alerts"), list)




