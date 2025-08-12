from __future__ import annotations

import os
import json
from fastapi.testclient import TestClient
from services.api.app.main import app


def main() -> None:
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_api_run.db")
    os.environ.setdefault("APP_ENV", "local")
    client = TestClient(app)
    period = "2025-06"
    # Seed verifications
    client.post(
        
        "/verifications",
        json={
            "org_id": 1,
            "date": f"{period}-05",
            "total_amount": 112.0,
            "currency": "SEK",
            "vat_code": "SE12",
            "entries": [
                {"account": "6071", "debit": 100.0, "credit": 0.0},
                {"account": "2641", "debit": 6.0, "credit": 0.0},
                {"account": "1910", "debit": 0.0, "credit": 112.0},
            ],
        },
    )
    client.post(
        
        "/verifications",
        json={
            "org_id": 1,
            "date": f"{period}-10",
            "total_amount": 125.0,
            "currency": "SEK",
            "vat_code": "SE25",
            "entries": [
                {"account": "5611", "debit": 100.0, "credit": 0.0},
                {"account": "2641", "debit": 12.5, "credit": 0.0},
                {"account": "1910", "debit": 0.0, "credit": 125.0},
            ],
        },
    )
    r = client.get("/reports/vat/declaration", params={"period": period})
    print(r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()





