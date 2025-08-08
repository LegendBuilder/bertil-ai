from __future__ import annotations

import re
from typing import Any


_PNR_REGEX = re.compile(r"\b(?:19|20)?\d{6}[-+]?\d{4}\b")


def mask_pii(text: str) -> str:
    """Mask Swedish personnummer patterns, keeping only last 4 digits.

    Examples:
      19860101-1234 -> ******-1234
      8601011234 -> ******-1234
    """
    def _repl(m: re.Match[str]) -> str:
        s = m.group(0)
        last4 = s[-4:]
        return "******-" + last4

    return _PNR_REGEX.sub(_repl, text)


def mask_in_structure(value: Any) -> Any:
    if isinstance(value, str):
        return mask_pii(value)
    if isinstance(value, dict):
        return {k: mask_in_structure(v) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_in_structure(v) for v in value]
    return value


