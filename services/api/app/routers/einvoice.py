from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..einvoice_bis import generate_bis, parse_bis


router = APIRouter(prefix="/einvoice", tags=["einvoice"])


@router.post("/generate")
async def generate(payload: dict) -> dict:
    try:
        xml = generate_bis(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    return {"xml": xml}


@router.post("/parse")
async def parse(payload: dict) -> dict:
    xml = payload.get("xml")
    if not xml:
        raise HTTPException(status_code=400, detail="xml required")
    try:
        data = parse_bis(xml)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    return {"invoice": data}













