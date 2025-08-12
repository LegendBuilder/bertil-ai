from __future__ import annotations

from services.api.app.main import app
from fastapi.testclient import TestClient


def test_documents_list_and_metrics():
    client = TestClient(app)
    r = client.get("/documents")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)

    m = client.get("/metrics/health")
    assert m.status_code == 200
    assert m.json().get("ok") is True














