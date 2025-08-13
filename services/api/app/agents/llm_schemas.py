from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError


class ReceiptExtractionResult(BaseModel):
    vendor: str
    total_amount: float = Field(ge=0)
    vat_amount: Optional[float] = Field(default=None, ge=0)
    vat_rate: Optional[float] = Field(default=None, ge=0, le=1)
    date: Optional[str] = None
    invoice_number: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class TaxOptimizationAction(BaseModel):
    type: str
    savings: float = Field(ge=0)
    reason: Optional[str] = None


class TaxOptimizationResult(BaseModel):
    total_tax_savings: float = Field(ge=0)
    optimizations: List[TaxOptimizationAction] = Field(default_factory=list)
    citations: Optional[List[dict]] = None


class ComplianceIssue(BaseModel):
    code: Optional[str] = None
    message: str
    severity: Optional[str] = Field(default="warning")


class ComplianceCheckResult(BaseModel):
    compliance_score: int = Field(ge=0, le=100)
    issues: List[str] | List[ComplianceIssue] = Field(default_factory=list)
    warnings: List[str] | List[ComplianceIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    citations: Optional[List[dict]] = None


class InsightItem(BaseModel):
    title: str
    message: str
    impact: Optional[float] = Field(default=None)
    urgency: Optional[str] = None
    action: Optional[str] = None
    citations: Optional[List[dict]] = None


class InsightsResult(BaseModel):
    insights: List[InsightItem]


def validate_data(model: type[BaseModel], data: dict) -> BaseModel:
    return model.model_validate(data)


