from __future__ import annotations

from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_session
from ..sie import generate_sie

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/sie")
async def export_sie(year: int, session: AsyncSession = Depends(get_session)) -> Response:
    content = await generate_sie(session, year)
    return Response(content=content, media_type="text/plain; charset=cp437")


