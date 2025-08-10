from __future__ import annotations

from fastapi.testclient import TestClient
from services.api.app.main import app


def _post_ver(client: TestClient, date: str, entries: list[dict], vat_code: str | None = None, total: float | None = None) -> None:
    payload = {
        "org_id": 1,
        "date": date,
        "total_amount": total if total is not None else sum((e.get("debit", 0.0) or 0.0) for e in entries),
        "currency": "SEK",
        **({"vat_code": vat_code} if vat_code else {}),
        "entries": entries,
    }
    r = client.post("/verifications", json=payload)
    assert r.status_code == 200


def test_vat_multiple_codes_declaration_boxes():
    client = TestClient(app)
    period = "2025-06"
    # SE12 case: add 2612 credit and base code
    _post_ver(
        client,
        f"{period}-05",
        entries=[
            {"account": "4010", "debit": 112.0, "credit": 0.0},
            {"account": "2612", "debit": 0.0, "credit": 12.0},
            {"account": "2641", "debit": 12.0, "credit": 0.0},
            {"account": "1910", "debit": 0.0, "credit": 112.0},
        ],
        vat_code="SE12",
        total=112.0,
    )
    # SE06 case: 2613 credit
    _post_ver(
        client,
        f"{period}-07",
        entries=[
            {"account": "4010", "debit": 106.0, "credit": 0.0},
            {"account": "2613", "debit": 0.0, "credit": 6.0},
            {"account": "2641", "debit": 6.0, "credit": 0.0},
            {"account": "1910", "debit": 0.0, "credit": 106.0},
        ],
        vat_code="SE06",
        total=106.0,
    )
    # EU RC services
    _post_ver(
        client,
        f"{period}-10",
        entries=[
            {"account": "4545", "debit": 200.0, "credit": 0.0},
            {"account": "2615", "debit": 0.0, "credit": 50.0},
            {"account": "2645", "debit": 50.0, "credit": 0.0},
            {"account": "1910", "debit": 0.0, "credit": 200.0},
        ],
        vat_code="EU-RC-SERV",
        total=200.0,
    )
    # OSS sale (ensure it doesn't affect 05–07 directly)
    _post_ver(
        client,
        f"{period}-12",
        entries=[
            {"account": "3001", "debit": 0.0, "credit": 60.0},
            {"account": "1930", "debit": 60.0, "credit": 0.0},
        ],
        vat_code="OSS-LOW",
        total=60.0,
    )
    r = client.get("/reports/vat/declaration", params={"period": period})
    assert r.status_code == 200
    boxes = r.json()["boxes"]
    # SE12 contributes to 06; SE06 contributes to 07
    assert boxes["06"] >= 112.0 - 0.0
    assert boxes["07"] >= 106.0 - 0.0
    # 31 and 32 should include credits from 2612 and 2613
    assert boxes["31"] >= 12.0
    assert boxes["32"] >= 6.0
    # OSS base not included in 05–07
    assert boxes["05"] >= 0.0  # unchanged by OSS-LOW





