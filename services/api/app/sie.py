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
    def _sanitize_account(acc: str | None) -> str:
        s = (acc or "").strip()
        if s.isdigit() and 3 <= len(s) <= 6:
            return s
        return "9999"

    for v in verifs:
        d: date = v.date
        ymd = f"{d.year:04d}{d.month:02d}{d.day:02d}"
        lines.append(f'#VER "V" {ymd} "Auto" 0')
        estmt = select(Entry).where(Entry.verification_id == v.id)
        entries = (await session.execute(estmt)).scalars().all()
        total = 0.0
        out_rows: list[tuple[str, float]] = []
        for e in entries:
            debit = float(e.debit) if e.debit is not None else 0.0
            credit = float(e.credit) if e.credit is not None else 0.0
            amount = round(debit - credit, 2)
            acc = _sanitize_account(e.account)
            out_rows.append((acc, amount))
            total = round(total + amount, 2)
        # Balance rounding differences by adding adjustment on 9999 if needed
        if abs(total) >= 0.01:
            out_rows.append(("9999", -total))
            total = 0.0
        for acc, amount in out_rows:
            lines.append(f"#TRANS {acc} {{}} {amount:.2f}")
    return "\n".join(lines) + "\n"


def parse_sie(content: str) -> list[dict]:
    """Very small SIE parser (VER/TRANS only) returning a list of verifications.

    Output format: [{"date": YYYY-MM-DD, "text": str, "entries": [{account, amount}...]}]
    Amount: positive = debit, negative = credit (we'll split later).
    """
    verifications: list[dict] = []
    current: dict | None = None
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#VER"):
            # Example: #VER "V" 20250115 "Text" 0
            parts = line.split()
            if len(parts) >= 3:
                ymd = parts[2]
                try:
                    y, m, d = int(ymd[0:4]), int(ymd[4:6]), int(ymd[6:8])
                    date_iso = f"{y:04d}-{m:02d}-{d:02d}"
                except Exception:
                    date_iso = "2025-01-01"
            else:
                date_iso = "2025-01-01"
            current = {"date": date_iso, "text": "", "entries": []}
            verifications.append(current)
        elif line.startswith("#TRANS") and current is not None:
            # Example: #TRANS 4000 {} 100.00
            parts = line.split()
            if len(parts) >= 3:
                account = parts[1]
                try:
                    amount = float(parts[-1].replace(",", "."))
                except Exception:
                    amount = 0.0
                current["entries"].append({"account": account, "amount": amount})
        else:
            continue
    return verifications

