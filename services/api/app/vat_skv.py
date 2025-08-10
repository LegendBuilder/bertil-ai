from __future__ import annotations

from datetime import date
from io import StringIO
from typing import Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Entry, Verification


def _boxes_from_period_rows(rows_accounts: list[tuple[str, float, float]], rows_codes: list[tuple[str | None, float]], year: int, month: int) -> Dict[str, float]:
    input_vat = 0.0
    output_vat_25 = 0.0
    output_vat_12 = 0.0
    output_vat_6 = 0.0
    for acc_str, s_deb, s_cred in rows_accounts:
        deb = float(s_deb or 0.0)
        cred = float(s_cred or 0.0)
        if acc_str.startswith("264"):
            input_vat += deb - cred
        if acc_str.startswith("261"):
            amt = cred - deb
            if acc_str.startswith("2611") or acc_str.startswith("2615") or acc_str.startswith("2610"):
                output_vat_25 += amt
            elif acc_str.startswith("2612"):
                output_vat_12 += amt
            elif acc_str.startswith("2613"):
                output_vat_6 += amt

    base25 = base12 = base6 = 0.0
    for code, total in rows_codes:
        c = (code or "").upper()
        amt = float(total or 0.0)
        if c == "SE25":
            base25 += amt
        elif c == "SE12":
            base12 += amt
        elif c == "SE06":
            base6 += amt
        # RC/EU-RC not included in 05–07; reflected via 2615/2645 already

    net = (output_vat_25 + output_vat_12 + output_vat_6) - input_vat
    return {
        "05": round(base25, 2),
        "06": round(base12, 2),
        "07": round(base6, 2),
        "30": round(output_vat_25, 2),
        "31": round(output_vat_12, 2),
        "32": round(output_vat_6, 2),
        "48": round(input_vat, 2),
        "49": round(net, 2),
    }


async def build_skv_file(session: AsyncSession, period: str) -> bytes:
    """Build a simple CSV file with SKV boxes suitable for pilot submission.
    Format: header row followed by `box;amount` lines.
    """
    dt = date.fromisoformat(period + "-01")
    end = date(dt.year, 12, 31) if dt.month == 12 else date(dt.year, dt.month + 1, 1)
    rows = (
        await session.execute(
            select(Entry.account, func.sum(Entry.debit), func.sum(Entry.credit))
            .join(Verification, Verification.id == Entry.verification_id)
            .where(Verification.date >= date(dt.year, dt.month, 1))
            .where(Verification.date < end)
            .group_by(Entry.account)
        )
    ).all()
    rows = [(str(acc), float(s_deb or 0.0), float(s_cred or 0.0)) for acc, s_deb, s_cred in rows]
    rows_code = (
        await session.execute(
            select(Verification.vat_code, func.sum(Verification.total_amount))
            .where(Verification.date >= date(dt.year, dt.month, 1))
            .where(Verification.date < end)
            .group_by(Verification.vat_code)
        )
    ).all()
    boxes = _boxes_from_period_rows(rows, rows_code, dt.year, dt.month)
    buf = StringIO()
    buf.write("box;amount\n")
    for k in ["05", "06", "07", "30", "31", "32", "48", "49"]:
        buf.write(f"{k};{boxes.get(k, 0.0):.2f}\n")
    return buf.getvalue().encode("utf-8")





