from __future__ import annotations

from fastapi.testclient import TestClient
from services.api.app.main import app


def test_review_queue_and_list():
    client = TestClient(app)
    q = client.post("/review/queue", json={"org_id": 1, "type": "autopost", "payload": {"doc_id": "abc"}, "confidence": 0.72})
    assert q.status_code == 200
    lid = q.json()["id"]
    lst = client.get("/review/inbox")
    assert lst.status_code == 200
    items = lst.json()["items"]
    assert any(it["id"] == lid for it in items)
    done = client.post(f"/review/{lid}/complete")
    assert done.status_code == 200





