from __future__ import annotations

from fastapi import APIRouter
from ..auth_utils import issue_jwt

router = APIRouter(prefix="/auth/bankid", tags=["auth"])


@router.post("/init")
async def bankid_init() -> dict:
    # Stub orderRef and autoStartToken for sandbox
    return {"orderRef": "stub-order-ref-ok", "autoStartToken": "stub-auto-token"}


@router.get("/status")
async def bankid_status(orderRef: str) -> dict:
    # Simple stub: completed when orderRef endswith 'ok'
    status = "complete" if orderRef.endswith("ok") else "pending"
    if status == "complete":
        user = {"subject": "SE-TEST-USER-123", "name": "Anna Andersson", "pnr_masked": "YYYYMMDD-XXXX"}
        token = issue_jwt(user["subject"], user["name"])  # noqa: S106 (stub secret in dev)
        return {"status": status, "user": user, "token": token}
    return {"status": status}


@router.get("/deeplink")
async def bankid_deeplink(orderRef: str, autostart: int = 1) -> dict:
    """Return a BankID app deep link (stub) for mobile redirect flows.

    In production, format: bankid:///?autostarttoken=<token>&redirect=<urlencoded>
    """
    # For stub, simulate a deep link
    link = f"bankid:///?autostarttoken={orderRef}&redirect=https%3A%2F%2Fapp.bertil-ai.se%2Fauth%2Fcb"
    return {"deeplink": link, "autostart": bool(autostart)}




