from __future__ import annotations

from typing import Dict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Entry, Verification, VatCode
from ..config import settings
from ..vat_skv import build_skv_file
from ..vat_mapping import summarize_codes


router = APIRouter(tags=["reports"])


@router.get("/trial-balance")
async def trial_balance(year: int, session: AsyncSession = Depends(get_session)) -> dict:
    # Aggregate entries for given year: sum(debit) - sum(credit) per account
    rows = (
        await session.execute(
            select(Entry.account, func.sum(Entry.debit), func.sum(Entry.credit))
            .join(Verification, Verification.id == Entry.verification_id)
            .where(func.extract("year", Verification.date) == year)
            .group_by(Entry.account)
            .order_by(Entry.account)
        )
    ).all()
    tb: Dict[str, float] = {}
    for account, sum_debit, sum_credit in rows:
        amount = float(sum_debit or 0.0) - float(sum_credit or 0.0)
        tb[account] = round(amount, 2)
    total = round(sum(tb.values()), 2)
    return {"year": year, "accounts": tb, "total": total}


@router.get("/reports/vat", response_model=None)
async def vat_report(
    period: str,  # format YYYY-MM
    format: str = "json",
    session: AsyncSession = Depends(get_session),
) -> dict | Response:
    # Parse period
    try:
        dt = datetime.strptime(period + "-01", "%Y-%m-%d").date()
    except ValueError as exc:
        return Response(status_code=400, content=f"invalid period: {period}")
    year = dt.year
    month = dt.month
    if month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, month + 1, 1)  # exclusive upper bound

    # Aggregate VAT from entries in the period
    rows = (
        await session.execute(
            select(Entry.account, func.sum(Entry.debit), func.sum(Entry.credit))
            .join(Verification, Verification.id == Entry.verification_id)
            .where(Verification.date >= date(year, month, 1))
            .where(Verification.date < end)
            .group_by(Entry.account)
        )
    ).all()
    outgoing = 0.0  # 261x-263x
    incoming = 0.0  # 264x
    for account, sum_debit, sum_credit in rows:
        acc = str(account)
        debit = float(sum_debit or 0.0)
        credit = float(sum_credit or 0.0)
        amount = debit - credit
        if acc.startswith("261") or acc.startswith("262") or acc.startswith("263"):
            # Outgoing VAT typically on credit; use absolute contribution
            outgoing += abs(amount)
        elif acc.startswith("264"):
            incoming += abs(amount)
    net = round(outgoing - incoming, 2)
    # Code-level breakdown (using verifications.vat_code when present)
    code_rows = (
        await session.execute(
            select(Verification.vat_code, func.count(Verification.id))
            .where(Verification.date >= date(year, month, 1))
            .where(Verification.date < end)
            .group_by(Verification.vat_code)
        )
    ).all()
    code_breakdown = {str(code or ""): int(cnt) for code, cnt in code_rows}

    payload = {
        "period": period,
        "outgoing_vat": round(outgoing, 2),
        "incoming_vat": round(incoming, 2),
        "net_vat": net,
        "currency": "SEK",
        "by_code": code_breakdown,
    }
    if format.lower() == "pdf":
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        left = 40
        top = height - 40
        c.setTitle(f"Momsrapport {period}")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left, top, f"Momsrapport {period}")
        c.setFont("Helvetica", 11)
        y = top - 32
        c.drawString(left, y, f"Utgående moms: {payload['outgoing_vat']:.2f} SEK")
        y -= 16
        c.drawString(left, y, f"Ingående moms: {payload['incoming_vat']:.2f} SEK")
        y -= 16
        c.drawString(left, y, f"Netto: {payload['net_vat']:.2f} SEK")
        c.showPage()
        c.save()
        pdf = buf.getvalue()
        buf.close()
        headers = {"Content-Disposition": f"inline; filename=moms_{period}.pdf"}
        return Response(content=pdf, media_type="application/pdf", headers=headers)
    return payload


@router.get("/reports/vat/declaration")
async def vat_declaration(
    period: str,  # YYYY-MM
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        dt = datetime.strptime(period + "-01", "%Y-%m-%d").date()
    except ValueError as exc:
        return Response(status_code=400, content=f"invalid period: {period}")
    year = dt.year
    month = dt.month
    if month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, month + 1, 1)

    # Input VAT (48): sum debit 264x
    rows = (
        await session.execute(
            select(Entry.account, func.sum(Entry.debit), func.sum(Entry.credit))
            .join(Verification, Verification.id == Entry.verification_id)
            .where(Verification.date >= date(year, month, 1))
            .where(Verification.date < end)
            .group_by(Entry.account)
        )
    ).all()
    input_vat = 0.0
    output_vat_25 = 0.0
    output_vat_12 = 0.0
    output_vat_6 = 0.0
    for acc, s_deb, s_cred in rows:
        acc_str = str(acc)
        deb = float(s_deb or 0.0)
        cred = float(s_cred or 0.0)
        if acc_str.startswith("264"):
            input_vat += deb - cred
        if acc_str.startswith("261"):
            # Map common accounts to 25/12/6 buckets
            # 2611/2615 ~ 25%, 2612 ~ 12%, 2613 ~ 6%
            amt = cred - deb
            if acc_str.startswith("2611") or acc_str.startswith("2615") or acc_str.startswith("2610"):
                output_vat_25 += amt
            elif acc_str.startswith("2612"):
                output_vat_12 += amt
            elif acc_str.startswith("2613"):
                output_vat_6 += amt

    # Base amounts by vat_code for domestic 25/12/6
    base25 = 0.0
    base12 = 0.0
    base6 = 0.0
    rows_code = (
        await session.execute(
            select(Verification.vat_code, func.sum(Verification.total_amount))
            .where(Verification.date >= date(year, month, 1))
            .where(Verification.date < end)
            .group_by(Verification.vat_code)
        )
    ).all()
    totals = summarize_codes(rows_code)
    base25, base12, base6 = totals["base25"], totals["base12"], totals["base6"]

    net = (output_vat_25 + output_vat_12 + output_vat_6) - input_vat
    return {
        "period": period,
        "boxes": {
            "05": round(base25, 2),
            "06": round(base12, 2),
            "07": round(base6, 2),
            "30": round(output_vat_25, 2),
            "31": round(output_vat_12, 2),
            "32": round(output_vat_6, 2),
            "48": round(input_vat, 2),
            "49": round(net, 2),
        },
        "notes": "MVP mapping; reverse charge/EU handled via 2615/2645 impact in output/input VAT."
    }



@router.get("/reports/vat/declaration/file")
async def vat_declaration_file(period: str, session: AsyncSession = Depends(get_session)):
    # Gate external format behind a flag until validated with Skatteverket
    if not settings.skv_file_export_enabled:
        from fastapi import Response
        return Response(status_code=501, content="skv file export disabled")
    content = await build_skv_file(session, period)
    from fastapi import Response
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=vat_{period}.csv"})

