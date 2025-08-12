from __future__ import annotations

from fastapi.testclient import TestClient
from typing import Any, Dict

from services.api.app.main import app


class _StubLLM:
    def __init__(self) -> None:
        pass

    async def generate_insights(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "insights": [
                {
                    "title": "Kassaflödesvarning",
                    "message": "Kommande betalningar överstiger kassaposition",
                    "impact": 10000,
                    "urgency": "immediate",
                    "action": "Skjut upp icke-kritiska inköp",
                    "citations": [],
                }
            ]
        }


def test_ai_enhanced_auto_post_basic() -> None:
    with TestClient(app) as client:
        payload = {
            "org_id": 1,
            "date": "2025-01-15",
            "total": 112.0,
            "vendor": "Kaffe AB",
        }
        r = client.post("/ai/enhanced/auto-post", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "id" in data and data.get("immutable_seq", 0) >= 1
        # Enhanced metadata from InvisibleBookkeeper
        assert data.get("automation_level") == "enhanced"


def test_ai_enhanced_pre_check_blocks_missing_fields() -> None:
    with TestClient(app) as client:
        payload = {
            "org_id": 1,
            "date": "2025-02-01",
            "total_amount": 100.0,
            # counterparty intentionally omitted
            "entries": [
                {"account": "1910", "debit": 100.0, "credit": 0.0},
                {"account": "4000", "debit": 0.0, "credit": 100.0},
            ],
        }
        r = client.post("/ai/enhanced/pre-check", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("can_proceed") is False
        assert any("Motpart" in s or "motpart" in s for s in body.get("issues", []))


def test_ai_enhanced_optimize_tax_and_report() -> None:
    with TestClient(app) as client:
        # Create a verification that looks like representation expense
        create = client.post(
            "/verifications",
            json={
                "org_id": 1,
                "date": "2025-03-10",
                "total_amount": 1000.0,
                "currency": "SEK",
                "counterparty": "Restaurang Prinsen",  # triggers representation rules
                "entries": [
                    {"account": "1910", "debit": 1000.0, "credit": 0.0},
                    {"account": "4000", "debit": 0.0, "credit": 1000.0},
                ],
            },
        )
        assert create.status_code == 200, create.text
        ver_id = create.json()["id"]

        # Optimize this verification
        r_opt = client.post(f"/ai/enhanced/optimize-tax/{ver_id}")
        assert r_opt.status_code == 200, r_opt.text
        out = r_opt.json()
        assert out.get("total_tax_savings", 0) >= 0.0
        # Report
        r_rep = client.get("/ai/enhanced/tax-report", params={"org_id": 1})
        assert r_rep.status_code == 200
        rep = r_rep.json()
        assert "total_potential_savings" in rep


def test_ai_enhanced_compliance_health_and_insights(monkeypatch) -> None:
    # Patch LLM to avoid network; return deterministic insights
    from services.api.app.agents import llm_integration as _llm
    from services.api.app.routers import ai_enhanced as _ai

    def _fake_get_llm_service():
        return _StubLLM()

    monkeypatch.setattr(_llm, "get_llm_service", _fake_get_llm_service)
    monkeypatch.setattr(_ai, "get_llm_service", _fake_get_llm_service)

    with TestClient(app) as client:
        r_ch = client.get("/ai/enhanced/compliance-health", params={"org_id": 1})
        assert r_ch.status_code == 200
        health = r_ch.json()
        assert "compliance_rate" in health

        r_ins = client.get("/ai/enhanced/insights", params={"org_id": 1})
        assert r_ins.status_code == 200
        ins = r_ins.json()
        assert ins.get("count", 0) >= 1

