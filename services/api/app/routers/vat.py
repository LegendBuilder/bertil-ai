from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_session
from ..models import VatCode


router = APIRouter(prefix="/vat", tags=["vat"])


@router.get("/codes")
async def list_vat_codes(session: AsyncSession = Depends(get_session)) -> dict:
    rows = (await session.execute(select(VatCode))).scalars().all()
    return {"items": [
        {
            "code": r.code,
            "description": r.description,
            "rate": float(r.rate),
            "reverse_charge": bool(r.reverse_charge),
        } for r in rows
    ]}








