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
    c.setTitle(f"Verifikationslista {year}")
    width, height = A4
    left_margin = 40
    top_margin = height - 40
    line_height = 14

    def draw_header() -> None:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left_margin, top_margin, f"Verifikationslista {year}")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, top_margin - 26, "Ver\tDatum\tMotpart\tBelopp")

    def draw_footer(page_num: int) -> None:
        c.setFont("Helvetica", 9)
        c.drawRightString(width - left_margin, 20, f"Sida {page_num}")

    # Fetch data
    stmt = select(Verification).where(Verification.date.between(date(year, 1, 1), date(year, 12, 31))).order_by(Verification.id)
    verifs = (await session.execute(stmt)).scalars().all()
    page_num = 1
    draw_header()
    c.setFont("Helvetica", 10)
    y = top_margin - 26 - line_height
    total_sum = 0.0
    for v in verifs:
        if y < 80:
            draw_footer(page_num)
            c.showPage()
            page_num += 1
            draw_header()
            c.setFont("Helvetica", 10)
            y = top_margin - 26 - line_height
        total_sum += float(v.total_amount)
        c.drawString(left_margin, y, f"V{v.immutable_seq}\t{v.date.isoformat()}\t{(v.counterparty or '')[:24]}\t{float(v.total_amount):.2f} {v.currency}")
        y -= line_height
        estmt = select(Entry).where(Entry.verification_id == v.id).order_by(Entry.id)
        entries = (await session.execute(estmt)).scalars().all()
        for e in entries:
            debit = float(e.debit or 0)
            credit = float(e.credit or 0)
            if abs(debit) < 1e-6 and abs(credit) < 1e-6:
                continue
            if y < 60:
                draw_footer(page_num)
                c.showPage()
                page_num += 1
                draw_header()
                c.setFont("Helvetica", 10)
                y = top_margin - 26 - line_height
            c.drawString(left_margin + 20, y, f"{e.account:>4}  D {debit:.2f}  K {credit:.2f}")
            y -= 12
        y -= 8

    # Footer total
    if y < 40:
        draw_footer(page_num)
        c.showPage()
        page_num += 1
        draw_header()
        y = top_margin - 26 - line_height
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, f"Summa: {total_sum:.2f} SEK")
    draw_footer(page_num)

    c.showPage()
    c.save()
    pdf = buf.getvalue()
    buf.close()

    headers = {"Content-Disposition": f"attachment; filename=verifikationslista_{year}.pdf"}
    return Response(content=pdf, media_type="application/pdf", headers=headers)

