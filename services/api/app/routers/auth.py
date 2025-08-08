from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/auth/bankid", tags=["auth"])


@router.post("/init")
async def bankid_init() -> dict:
    # Stub orderRef and autoStartToken for sandbox
    return {"orderRef": "stub-order-ref", "autoStartToken": "stub-auto-token"}


@router.get("/status")
async def bankid_status(orderRef: str) -> dict:
    # Simple stub: completed when orderRef endswith 'ok'
    status = "complete" if orderRef.endswith("ok") else "pending"
    user = (
        {"subject": "SE-TEST-USER-123", "name": "Anna Andersson", "pnr_masked": "YYYYMMDD-XXXX"}
        if status == "complete"
        else None
    )
    return {"status": status, "user": user}


