from __future__ import annotations

from services.api.app.agents.llm_schemas import ReceiptExtractionResult, TaxOptimizationResult, ComplianceCheckResult, InsightsResult


def test_receipt_extraction_schema_sample():
    data = {
        "vendor": "Kaffe AB",
        "total_amount": 123.45,
        "vat_amount": 13.72,
        "vat_rate": 0.12,
        "date": "2025-01-15",
        "confidence": 0.9,
    }
    parsed = ReceiptExtractionResult.model_validate(data)
    assert parsed.vendor == "Kaffe AB"


def test_tax_optimization_schema_sample():
    data = {
        "total_tax_savings": 120.0,
        "optimizations": [{"type": "representation", "savings": 120.0, "reason": "50% rule"}],
    }
    parsed = TaxOptimizationResult.model_validate(data)
    assert parsed.total_tax_savings >= 0


def test_compliance_schema_sample():
    data = {
        "compliance_score": 90,
        "issues": [],
        "warnings": [],
        "recommendations": [],
    }
    parsed = ComplianceCheckResult.model_validate(data)
    assert parsed.compliance_score == 90


def test_insights_schema_sample():
    data = {"insights": [{"title": "Trend", "message": "Costs rising"}]}
    parsed = InsightsResult.model_validate(data)
    assert len(parsed.insights) == 1


