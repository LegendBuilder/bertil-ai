from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/auth/bankid", tags=["auth"])


@router.post("/init")
async def bankid_init() -> dict:
    # Stub orderRef and autoStartToken for sandbox
    return {"orderRef": "stub-order-ref", "autoStartToken": "stub-auto-token"}


@router.get("/status")
async def bankid_status(orderRef: str) -> dict:
    # Simple rotating stub: pretend completed if orderRef endswith 'ok'
    status = "complete" if orderRef.endswith("ok") else "pending"
    user = {"name": "Test Användare", "personnummer": "***-****"} if status == "complete" else None
    return {"status": status, "user": user}


