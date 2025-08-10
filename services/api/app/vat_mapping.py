from __future__ import annotations

from typing import Dict, Iterable, Tuple


RC_PREFIXES = ("RC", "EU-RC")
OSS_PREFIX = "OSS"


def summarize_codes(code_totals: Iterable[Tuple[str | None, float]]) -> Dict[str, float]:
    base25 = base12 = base6 = 0.0
    rc_base = 0.0
    oss_sales = 0.0
    for code, total in code_totals:
        c = (code or "").upper()
        amt = float(total or 0.0)
        if c == "SE25":
            base25 += amt
        elif c == "SE12":
            base12 += amt
        elif c == "SE06":
            base6 += amt
        elif any(c.startswith(p) for p in RC_PREFIXES):
            rc_base += amt
        elif c.startswith(OSS_PREFIX):
            oss_sales += amt
    return {
        "base25": round(base25, 2),
        "base12": round(base12, 2),
        "base6": round(base6, 2),
        "rc_base": round(rc_base, 2),
        "oss_sales": round(oss_sales, 2),
    }





