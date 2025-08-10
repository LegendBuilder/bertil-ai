from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Tuple

from .config import settings


@dataclass
class FallbackField:
    key: str
    value: str
    confidence: float


async def extract_fields_with_llm(text: str) -> List[Tuple[str, str, float]]:
    if not settings.llm_fallback_enabled:
        return []
    # Stub implementation: in real use, call provider with a strict JSON schema
    # Return empty to avoid accidental use without explicit enabling
    return []








