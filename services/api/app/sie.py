from __future__ import annotations

from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Entry, Verification


async def generate_sie(session: AsyncSession, year: int) -> str:
    header = [
        "#FLAGGA 0",
        "#PROGRAM BERTIL 0.1",
        "#FORMAT PC8",
        "#SIETYP 4",
    ]
    lines: list[str] = header
    stmt = select(Verification).where(func.extract("year", Verification.date) == year).order_by(Verification.id)
    verifs = (await session.execute(stmt)).scalars().all()
    for v in verifs:
        d: date = v.date
        ymd = f"{d.year:04d}{d.month:02d}{d.day:02d}"
        lines.append(f'#VER "V" {ymd} "Auto" 0')
        estmt = select(Entry).where(Entry.verification_id == v.id)
        entries = (await session.execute(estmt)).scalars().all()
        for e in entries:
            debit = float(e.debit) if e.debit is not None else 0.0
            credit = float(e.credit) if e.credit is not None else 0.0
            amount = debit - credit
            # Minimal SIE-like TRANS row
            lines.append(f"#TRANS {e.account} {{}} {amount:.2f}")
    return "\n".join(lines) + "\n"


