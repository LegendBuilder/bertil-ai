from fastapi.testclient import TestClient

from services.api.app.main import app


def test_metrics_event_increments_counts() -> None:
    client = TestClient(app)
    # Reset state is not exposed; rely on isolated process for tests and unique name
    name = "test_event_example"
    r1 = client.post("/metrics/event", json={"name": name, "params": {"x": 1}, "platform": "web"})
    assert r1.status_code == 200, r1.text
    c1 = r1.json()["count"]

    r2 = client.post("/metrics/event", json={"name": name})
    assert r2.status_code == 200, r2.text
    c2 = r2.json()["count"]

    assert c2 == c1 + 1

    stats = client.get("/metrics/event/stats").json()
    assert stats["events"][name] >= 2


def test_metrics_event_missing_name_400() -> None:
    client = TestClient(app)
    r = client.post("/metrics/event", json={})
    assert r.status_code == 400
    body = r.json()
    assert body.get("detail", {}).get("error") == "missing_name"



