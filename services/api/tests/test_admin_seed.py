from __future__ import annotations

from services.api.app.main import app
from fastapi.testclient import TestClient


def test_admin_seed_vendors():
    client = TestClient(app)
    r = client.post("/admin/seed/vendors")
    assert r.status_code == 200
    body = r.json()
    assert "inserted" in body










