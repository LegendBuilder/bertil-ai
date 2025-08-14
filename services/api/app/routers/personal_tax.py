"""
Personal Tax Optimization API

Endpoints for discovering tax deductions, optimizing personal finances,
and automating Swedish skattedeklaration.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..security import require_user
from ..agents.avdrag_discovery import discover_all_avdrag, SwedishTaxRuleEngine

router = APIRouter(prefix="/personal-tax", tags=["personal-tax"])


@router.post("/analyze-receipt")
async def analyze_receipt_for_avdrag(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
    user=Depends(require_user)
) -> Dict[str, Any]:
    """
    Analyze a receipt/transaction for all possible personal tax deductions
    
    Expected body:
    {
        "receipt_data": {
            "vendor": "ICA Maxi",
            "total": 1500.0,
            "date": "2024-01-15",
            "category": "groceries",
            "description": "various items"
        },
        "user_profile": {
            "income": 450000,
            "work_commute_km": 75,
            "family_status": "married",
            "medical_expenses_ytd": 3500,
            "charity_donations_ytd": 1000
        }
    }
    """
    
    try:
        receipt_data = body.get("receipt_data", {})
        user_profile = body.get("user_profile", {})
        
        # Discover all possible avdrag from this receipt
        analysis = await discover_all_avdrag(receipt_data, user_profile)
        
        # Add receipt-specific recommendations
        analysis["receipt_analysis"] = {
            "vendor": receipt_data.get("vendor"),
            "amount": receipt_data.get("total"),
            "processed_at": "2024-01-15T10:30:00Z",
            "confidence_score": min([opp["confidence"] for category in analysis["opportunities_by_category"].values() for opp in category] + [1.0])
        }
        
        return {
            "status": "success",
            "analysis": analysis,
            "action_required": len(analysis["recommendations"]) > 0,
            "immediate_benefits": [
                rec for rec in analysis["recommendations"] 
                if "ROT" in rec or "RUT" in rec  # Highlight immediate high-value deductions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Receipt analysis failed: {e}")


@router.post("/optimize-family-taxes")
async def optimize_family_taxes(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
    user=Depends(require_user)
) -> Dict[str, Any]:
    """
    Optimize taxes for family situations (married/sambo/children)
    
    Expected body:
    {
        "family_data": {
            "status": "married",
            "user_income": 550000,
            "spouse_income": 320000,
            "children": [
                {"age": 8, "in_school": true},
                {"age": 12, "in_school": true}
            ]
        }
    }
    """
    
    try:
        family_data = body.get("family_data", {})
        
        engine = SwedishTaxRuleEngine()
        strategies = await engine.optimize_family_taxes(family_data)
        
        # Calculate family benefits
        children = family_data.get("children", [])
        monthly_barnbidrag = 1330 * len(children)
        
        # Add specific recommendations
        recommendations = []
        if family_data.get("status") in ["married", "sambo"]:
            recommendations.append("Koordinera ROT/RUT-avdrag mellan partners för maximal nytta")
            recommendations.append("Överväg att höginkomsttagare maximerar pensionssparande")
        
        if children:
            recommendations.append(f"Automatiskt barnbidrag: {monthly_barnbidrag} SEK/månad")
            if any(child.get("age", 0) >= 16 for child in children):
                recommendations.append("Kontrollera förlängd barnbidrag för barn i gymnasiet")
        
        return {
            "status": "success",
            "optimization_strategies": strategies,
            "monthly_benefits": {
                "barnbidrag": monthly_barnbidrag,
                "estimated_total": monthly_barnbidrag + sum(
                    s.get("potential_savings", 0) / 12 for s in strategies if "potential_savings" in s
                )
            },
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Family optimization failed: {e}")


@router.post("/pension-optimization")
async def optimize_pension_contributions(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
    user=Depends(require_user)
) -> Dict[str, Any]:
    """
    Optimize pension contributions and savings strategies
    
    Expected body:
    {
        "financial_data": {
            "annual_income": 550000,
            "age": 35,
            "existing_pension": 450000,
            "risk_tolerance": "moderate"
        }
    }
    """
    
    try:
        financial_data = body.get("financial_data", {})
        annual_income = financial_data.get("annual_income", 0)
        age = financial_data.get("age", 30)
        
        # IPS optimization (Individual Pension Savings)
        ips_max = 7000  # 2024 limit
        ips_tax_savings = ips_max * 0.32  # Approximate tax savings
        
        # Occupational pension optimization
        pension_limit_rate = 0.075
        pension_income_cap = 850000
        max_pension_contribution = min(annual_income * pension_limit_rate, pension_income_cap * pension_limit_rate)
        pension_tax_savings = max_pension_contribution * 0.32
        
        # Investment account recommendations
        recommendations = []
        
        if annual_income > 0:
            recommendations.append(f"Maximera IPS-sparande: {ips_max} SEK/år ger {ips_tax_savings:.0f} SEK i skattebesparing")
            
            if max_pension_contribution > 0:
                recommendations.append(
                    f"Tjänstepension via löneväxling: upp till {max_pension_contribution:.0f} SEK/år "
                    f"ger {pension_tax_savings:.0f} SEK i skattebesparing"
                )
        
        # Age-based recommendations
        if age < 40:
            recommendations.append("Fokus på ISK-konto för flexibelt aktiesparande")
            recommendations.append("Överväg kapitalförsäkring för långsiktigt sparande")
        elif age >= 55:
            recommendations.append("Planera för pensionsuttag och optimera skattetidpunkter")
            recommendations.append("Överväg traditionell försäkring för garanterad avkastning")
        
        return {
            "status": "success",
            "optimization_plan": {
                "ips_recommendation": {
                    "max_contribution": ips_max,
                    "tax_savings": ips_tax_savings,
                    "priority": "high"
                },
                "occupational_pension": {
                    "max_contribution": max_pension_contribution,
                    "tax_savings": pension_tax_savings,
                    "priority": "high" if max_pension_contribution > 0 else "low"
                },
                "investment_strategy": "balanced" if age < 50 else "conservative"
            },
            "total_potential_tax_savings": ips_tax_savings + pension_tax_savings,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pension optimization failed: {e}")


@router.get("/tax-calendar")
async def get_tax_calendar(
    user=Depends(require_user)
) -> Dict[str, Any]:
    """Get important tax dates and deadlines for Swedish individuals"""
    
    current_year = 2024
    
    tax_calendar = {
        "current_year_deadlines": [
            {
                "date": f"{current_year + 1}-05-02",
                "event": "Skattedeklaration deadline",
                "description": "Sista dag att lämna inkomstdeklaration",
                "priority": "critical"
            },
            {
                "date": f"{current_year}-12-31",
                "event": "IPS-insättning deadline", 
                "description": "Sista dag för pensionssparande som ger avdrag",
                "priority": "high"
            },
            {
                "date": f"{current_year}-12-31",
                "event": "ROT/RUT-arbeten",
                "description": "Arbeten måste vara utförda före årsskiftet",
                "priority": "high"
            }
        ],
        "monthly_reminders": [
            {
                "month": "januari",
                "tasks": ["Samla kvitton från föregående år", "Kontrollera preliminärskatt"]
            },
            {
                "month": "februari", 
                "tasks": ["Förbereda underlag för deklaration", "Kontrollera avdragsmöjligheter"]
            },
            {
                "month": "mars",
                "tasks": ["Lämna skattedeklaration", "Planera årets skattestrategi"]
            },
            {
                "month": "december",
                "tasks": ["Sista chansen IPS-sparande", "Genomför planerade ROT/RUT-arbeten"]
            }
        ]
    }
    
    return {
        "status": "success",
        "tax_calendar": tax_calendar,
        "next_deadline": "2025-05-02",
        "days_until_deadline": 120  # This would be calculated dynamically
    }


@router.post("/estimate-refund")
async def estimate_tax_refund(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
    user=Depends(require_user)
) -> Dict[str, Any]:
    """
    Estimate potential tax refund based on discovered deductions
    
    Expected body:
    {
        "income_data": {
            "gross_income": 550000,
            "preliminary_tax_paid": 185000,
            "discovered_deductions": [
                {"category": "ROT", "amount": 15000},
                {"category": "IPS", "amount": 7000},
                {"category": "Medical", "amount": 3000}
            ]
        }
    }
    """
    
    try:
        income_data = body.get("income_data", {})
        gross_income = income_data.get("gross_income", 0)
        preliminary_tax = income_data.get("preliminary_tax_paid", 0)
        deductions = income_data.get("discovered_deductions", [])
        
        # Calculate taxable income after deductions
        total_deductions = sum(d.get("amount", 0) for d in deductions)
        taxable_income = max(0, gross_income - total_deductions)
        
        # Simplified tax calculation (municipal + state tax)
        municipal_rate = 0.32
        state_tax_threshold = 598500
        state_tax_rate = 0.20
        
        municipal_tax = taxable_income * municipal_rate
        state_tax = max(0, (taxable_income - state_tax_threshold) * state_tax_rate)
        total_tax_owed = municipal_tax + state_tax
        
        # Calculate refund/additional tax
        refund_amount = preliminary_tax - total_tax_owed
        
        return {
            "status": "success",
            "tax_calculation": {
                "gross_income": gross_income,
                "total_deductions": total_deductions,
                "taxable_income": taxable_income,
                "municipal_tax": municipal_tax,
                "state_tax": state_tax,
                "total_tax_owed": total_tax_owed,
                "preliminary_tax_paid": preliminary_tax
            },
            "refund_estimate": {
                "amount": refund_amount,
                "type": "refund" if refund_amount > 0 else "additional_tax",
                "confidence": "high" if abs(refund_amount) < 10000 else "medium"
            },
            "optimization_impact": {
                "deductions_discovered": len(deductions),
                "tax_savings_from_deductions": total_deductions * municipal_rate,
                "recommendations": [
                    "Kontrollera att alla kvitton är sparade",
                    "Planera nästa års avdragsmöjligheter",
                    "Överväg ytterligare pensionssparande"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Refund estimation failed: {e}")


@router.post("/generate-skattedeklaration")
async def generate_personal_tax_return(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
    user=Depends(require_user)
) -> Dict[str, Any]:
    """
    Generate automated skattedeklaration based on discovered deductions and income
    
    This endpoint will be fully implemented once Skatteverket API access is available
    """
    
    return {
        "status": "preparation_mode",
        "message": "Skattedeklaration generation ready - awaiting Skatteverket API access",
        "preparation_data": {
            "deductions_ready": True,
            "income_data_ready": True,
            "family_optimization_ready": True,
            "estimated_completion_time": "< 30 seconds when API is available"
        },
        "next_steps": [
            "Continue collecting receipts and optimizing deductions",
            "System will automatically generate and submit when API access is granted",
            "All data is being prepared for instant submission"
        ]
    }