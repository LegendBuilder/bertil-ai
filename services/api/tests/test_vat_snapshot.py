from __future__ import annotations

from datetime import date
from fastapi.testclient import TestClient
from services.api.app.main import app


def test_vat_declaration_snapshot_domestic_and_rc():
    with TestClient(app) as client:
        period = "2025-05"
        # Domestic 25%
        client.post(
        "/verifications",
        json={
            "org_id": 1,
            "date": f"{period}-10",
            "total_amount": 100.0,
            "currency": "SEK",
            "vat_code": "SE25",
            "entries": [
                {"account": "4000", "debit": 100.0, "credit": 0.0},
                {"account": "2611", "debit": 0.0, "credit": 25.0},
                {"account": "2641", "debit": 25.0, "credit": 0.0},
                {"account": "1910", "debit": 0.0, "credit": 100.0},
            ],
        },
    )
        # Reverse charge base
        client.post(
        "/verifications",
        json={
            "org_id": 1,
            "date": f"{period}-12",
            "total_amount": 200.0,
            "currency": "SEK",
            "vat_code": "RC25",
            "entries": [
                {"account": "4056", "debit": 200.0, "credit": 0.0},
                {"account": "2615", "debit": 0.0, "credit": 50.0},
                {"account": "2645", "debit": 50.0, "credit": 0.0},
                {"account": "1910", "debit": 0.0, "credit": 200.0},
            ],
        },
    )
        r = client.get("/reports/vat/declaration", params={"period": period})
        assert r.status_code == 200
        boxes = r.json()["boxes"]
        # Snapshot expectations: 05 includes SE25 base (>=100), RC base excluded from 05; 30 & 48 reflect 2611/2615 and 2641/2645
        assert boxes["05"] >= 100.0
        assert boxes["30"] >= 25.0
        assert boxes["48"] >= 25.0


def test_vat_declaration_representation_and_drivmedel_edges():
    with TestClient(app) as client:
        period = "2025-06"
        # Representation (50% non-deductible VAT on meals). We simulate via base SE12 and input VAT on 2641
        client.post(
        "/verifications",
        json={
            "org_id": 1,
            "date": f"{period}-05",
            "total_amount": 112.0,  # 100 base + 12 VAT
            "currency": "SEK",
            "vat_code": "SE12",
            "entries": [
                {"account": "6071", "debit": 100.0, "credit": 0.0},
                {"account": "2641", "debit": 6.0, "credit": 0.0},   # only 50% deductible in practice
                {"account": "1910", "debit": 0.0, "credit": 112.0},
            ],
        },
    )
        # Drivmedel (limited deductibility) — simulate as SE25 with reduced input VAT debit
        client.post(
        "/verifications",
        json={
            "org_id": 1,
            "date": f"{period}-10",
            "total_amount": 125.0,  # 100 + 25 VAT
            "currency": "SEK",
            "vat_code": "SE25",
            "entries": [
                {"account": "5611", "debit": 100.0, "credit": 0.0},
                {"account": "2641", "debit": 12.5, "credit": 0.0},  # 50% deductible VAT
                {"account": "1910", "debit": 0.0, "credit": 125.0},
            ],
        },
    )
        r = client.get("/reports/vat/declaration", params={"period": period})
        assert r.status_code == 200
        boxes = r.json()["boxes"]
        # Base boxes reflect full bases; input VAT (48) reflects partial deductibles
        assert boxes["06"] >= 100.0
        assert boxes["05"] >= 100.0
        # Input VAT should equal 6.0 + 12.5 = 18.5
        assert abs(boxes["48"] - 18.5) < 0.01



