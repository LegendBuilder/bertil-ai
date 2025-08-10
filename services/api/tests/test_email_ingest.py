from __future__ import annotations

import os
from fastapi.testclient import TestClient
from services.api.app.main import app


def test_email_ingest_stub_disabled():
    client = TestClient(app)
    r = client.post("/email/ingest")
    assert r.status_code == 501


def test_email_ingest_imap_config_missing():
    client = TestClient(app)
    r = client.post("/email/ingest/imap")
    assert r.status_code in (400, 501)


