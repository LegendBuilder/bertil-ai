from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class MappingDecision:
    expense_account: str
    vat_rate: float  # 0.0..1.0
    reason: str


def suggest_account_and_vat(vendor: str | None, total_amount: float) -> MappingDecision:
    v = (vendor or "").lower()
    if any(k in v for k in ["kaffe", "café", "cafe", "fika", "lunch"]):
        return MappingDecision("5811", 0.12, "Leverantör antyder representation (12% moms)")
    if "taxi" in v:
        return MappingDecision("5611", 0.06, "Taxi-resor (6% moms)")
    if any(k in v for k in ["shell", "circle k", "preem", "okq8"]):
        return MappingDecision("5611", 0.25, "Drivmedel (25% moms)")
    return MappingDecision("4000", 0.25, "Standard inköp (25% moms)")


def build_entries(total_amount: float, expense_account: str, vat_rate: float) -> list[dict]:
    if vat_rate <= 0:
        return [
            {"account": expense_account, "debit": round(total_amount, 2), "credit": 0.0},
            {"account": "1910", "debit": 0.0, "credit": round(total_amount, 2)},
        ]
    net = round(total_amount / (1.0 + vat_rate), 2)
    vat = round(total_amount - net, 2)
    return [
        {"account": expense_account, "debit": net, "credit": 0.0},
        {"account": "2641", "debit": vat, "credit": 0.0},  # Ingående moms
        {"account": "1910", "debit": 0.0, "credit": round(total_amount, 2)},
    ]


