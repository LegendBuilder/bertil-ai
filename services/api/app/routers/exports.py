from __future__ import annotations

from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_session
from ..sie import generate_sie
from sqlalchemy import select
from ..models import Verification, Entry
from datetime import date

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/sie")
async def export_sie(year: int, session: AsyncSession = Depends(get_session)) -> Response:
    content = await generate_sie(session, year)
    return Response(content=content, media_type="text/plain; charset=cp437")


@router.get("/verifications.pdf")
async def export_verifications_pdf(year: int, session: AsyncSession = Depends(get_session)) -> Response:
    # Generate a simple PDF report of verifications for the year
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Fetch data
    stmt = select(Verification).where(Verification.date.between(date(year, 1, 1), date(year, 12, 31))).order_by(Verification.id)
    verifs = (await session.execute(stmt)).scalars().all()

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Verifikationslista {year}")
    y -= 20
    c.setFont("Helvetica", 10)
    for v in verifs:
        if y < 80:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, f"Verifikationslista {year}")
            y -= 20
            c.setFont("Helvetica", 10)
        c.drawString(40, y, f"#{v.immutable_seq}  {v.date.isoformat()}  {v.counterparty or ''}  {float(v.total_amount):.2f} {v.currency}")
        y -= 14
        estmt = select(Entry).where(Entry.verification_id == v.id).order_by(Entry.id)
        entries = (await session.execute(estmt)).scalars().all()
        for e in entries:
            if y < 60:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 10)
            c.drawString(60, y, f"{e.account:>4}  D {float(e.debit or 0):.2f}  K {float(e.credit or 0):.2f}")
            y -= 12
        y -= 8

    c.showPage()
    c.save()
    pdf = buf.getvalue()
    buf.close()

    headers = {"Content-Disposition": f"attachment; filename=verifikationslista_{year}.pdf"}
    return Response(content=pdf, media_type="application/pdf", headers=headers)

