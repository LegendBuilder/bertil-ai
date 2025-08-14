import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_receipt_endpoint():
    """Test the analyze receipt endpoint"""
    payload = {
        "receipt_data": {
            "vendor": "ICA",
            "total": 500.0,
            "date": "2025-01-15",
            "category": "medical",
            "description": "Prescription medicine"
        },
        "user_profile": {
            "income": 450000,
            "family_status": "single",
            "age": 35,
            "home_owner": True,
            "work_commute_km": 50,
            "medical_expenses_ytd": 0
        }
    }
    
    response = client.post("/personal-tax/analyze-receipt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "total_potential_savings" in data["analysis"]


def test_tax_calendar_endpoint():
    """Test the tax calendar endpoint"""
    response = client.get("/personal-tax/tax-calendar")
    assert response.status_code == 200
    data = response.json()
    assert "tax_year" in data
    assert "important_dates" in data


def test_optimize_family_taxes_endpoint():
    """Test the family tax optimization endpoint"""
    payload = {
        "family_data": {
            "status": "married",
            "user_income": 450000,
            "spouse_income": 320000,
            "children": []
        }
    }
    
    response = client.post("/personal-tax/optimize-family-taxes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "optimization" in data
    assert "potential_savings" in data["optimization"]


def test_pension_optimization_endpoint():
    """Test the pension optimization endpoint"""
    payload = {
        "financial_data": {
            "annual_income": 450000,
            "age": 35,
            "existing_pension": 450000,
            "risk_tolerance": "moderate"
        }
    }
    
    response = client.post("/personal-tax/pension-optimization", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "projected_savings" in data


def test_estimate_refund_endpoint():
    """Test the refund estimation endpoint"""
    payload = {
        "income_data": {
            "gross_income": 450000,
            "preliminary_tax_paid": 144000,
            "discovered_deductions": [
                {"category": "ROT", "amount": 15000},
                {"category": "IPS", "amount": 7000}
            ]
        }
    }
    
    response = client.post("/personal-tax/estimate-refund", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "estimated_refund" in data
    assert "confidence_level" in data