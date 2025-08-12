from __future__ import annotations

from io import BytesIO
from services.api.app.main import app
from fastapi.testclient import TestClient


def test_sie_import_roundtrip():
    client = TestClient(app)
    sie = (
        "#FLAGGA 0\n"
        "#SIETYP 4\n"
        "#VER \"V\" 20250115 \"Auto\" 0\n"
        "#TRANS 4000 {} 100.00\n"
        "#TRANS 1910 {} -100.00\n"
    ).encode("cp437")
    files = {"file": ("test.se", BytesIO(sie), "text/plain")}
    r = client.post("/imports/sie", files=files)
    assert r.status_code == 200
    assert r.json()["imported"] >= 1














