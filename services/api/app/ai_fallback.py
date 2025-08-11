from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import List, Tuple, Any, Dict

from .config import settings


@dataclass
class FallbackField:
    key: str
    value: str
    confidence: float


def _map_response_to_fields(resp: Dict[str, Any]) -> List[Tuple[str, str, float]]:
    """Map a generic extraction dict to a list of (key, value, confidence)."""
    if not isinstance(resp, dict):
        return []
    confidence = float(resp.get("confidence", settings.llm_extraction_threshold))
    out: List[Tuple[str, str, float]] = []

    # Common key variants
    vendor = resp.get("vendor") or resp.get("company") or resp.get("counterparty")
    if vendor:
        out.append(("vendor", str(vendor), confidence))

    total = (
        resp.get("total")
        or resp.get("total_amount")
        or resp.get("amount")
        or resp.get("belopp")
    )
    if total is not None:
        out.append(("total", str(total), confidence))

    date = resp.get("date") or resp.get("datum")
    if date:
        out.append(("date", str(date), confidence))

    vat_rate = resp.get("vat_rate") or resp.get("moms_sats")
    if vat_rate is not None:
        out.append(("vat_rate", str(vat_rate), confidence))

    vat_amount = resp.get("vat_amount") or resp.get("moms_belopp")
    if vat_amount is not None:
        out.append(("vat_amount", str(vat_amount), confidence))

    invoice_no = resp.get("invoice_number") or resp.get("fakturanummer")
    if invoice_no:
        out.append(("invoice_number", str(invoice_no), confidence))

    return out


async def extract_fields_with_llm(text: str) -> List[Tuple[str, str, float]]:
    """Attempt LLM-based field extraction for low-confidence OCR cases.

    Returns empty list unless explicitly enabled via settings.llm_fallback_enabled.
    """
    if not settings.llm_fallback_enabled:
        return []

    provider = (settings.llm_provider or os.getenv("LLM_PROVIDER", "")).lower().strip()

    # Strict, short prompt to reduce cost and enforce JSON
    extraction_prompt = f"""
    Extrahera strukturerad data från följande svensk kvittotext.

    Text:
    {text[:2000]}

    Returnera ENDAST JSON-objekt med fälten:
    {{
      "vendor": "företagsnamn",
      "total_amount": nummer,
      "vat_amount": nummer eller 0,
      "vat_rate": 0.25/0.12/0.06 eller 0,
      "date": "YYYY-MM-DD",
      "invoice_number": "om finns",
      "confidence": 0.0-1.0
    }}
    """

    try:
        if provider == "openrouter":
            # Use OpenRouter optimized path (Swedish model, forced JSON)
            from .agents.openrouter_integration import get_openrouter_client

            client = get_openrouter_client()
            resp = await client._call_openrouter(  # type: ignore[attr-defined]
                model=client.models.get("swedish", "meta-llama/llama-3.1-70b-instruct:free"),
                prompt=extraction_prompt,
                task_type="extraction",
                temperature=0.1,
            )
            return _map_response_to_fields(resp)

        else:
            # Fallback to generic LLM service (OpenAI/Anthropic/Local)
            from .agents.llm_integration import get_llm_service

            llm = get_llm_service()
            resp = await llm.extract_receipt_data(text)
            return _map_response_to_fields(resp)

    except Exception:
        # On any error, return empty to force manual review
        return []










