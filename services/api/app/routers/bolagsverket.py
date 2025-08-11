from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/bolagsverket", tags=["bolagsverket"])


@router.post("/submit")
async def submit_annual_report(payload: dict[str, Any]) -> dict:
    """Stub endpoint for Bolagsverket e-filing.

    Accepts a JSON payload (e.g., metadata + XBRL bytes in future) and returns a queued receipt.
    """
    receipt = {
        "id": f"BV-{int(datetime.utcnow().timestamp())}",
        "status": "queued",
        "message": "E-inlämning (stub) kölagd",
    }
    return receipt










