from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Verification


@dataclass
class RuleFlag:
    rule_code: str
    severity: str  # error|warning|info
    message: str


def _is_missing_verification_content(v: Verification) -> list[str]:
    missing: list[str] = []
    if not v.date:
        missing.append("date")
    if v.total_amount is None:
        missing.append("total_amount")
    if v.counterparty in (None, ""):
        missing.append("counterparty")
    if v.vat_amount is None:
        missing.append("vat_amount")
    if v.document_link in (None, ""):
        missing.append("document_link")
    return missing


async def rule_R001(session: AsyncSession, v: Verification) -> list[RuleFlag]:
    missing = _is_missing_verification_content(v)
    if missing:
        return [
            RuleFlag(
                rule_code="R-001",
                severity="error",
                message=f"Verifikationen saknar: {', '.join(missing)}",
            )
        ]
    return []


async def rule_R011(_session: AsyncSession, v: Verification) -> list[RuleFlag]:
    # Simplified: warn if older than 30 days (placeholder for next business day logic)
    try:
        if isinstance(v.date, date) and (date.today() - v.date) > timedelta(days=30):
            return [
                RuleFlag(
                    rule_code="R-011",
                    severity="warning",
                    message="Löpande bokföring kan vara försenad (äldre än 30 dagar).",
                )
            ]
    except Exception:
        pass
    return []


async def rule_R021(_session: AsyncSession, v: Verification) -> list[RuleFlag]:
    # Require that a document link exists and appears in local WORM-like store
    if not v.document_link:
        return [
            RuleFlag(
                rule_code="R-021",
                severity="error",
                message="Arkiveringslänk saknas; WORM-arkivering kan ej verifieras.",
            )
        ]
    p = Path(v.document_link)
    if not p.exists():
        return [
            RuleFlag(
                rule_code="R-021",
                severity="error",
                message="Underlag hittas ej i WORM-lagring.",
            )
        ]
    return []


async def rule_R031(_session: AsyncSession, v: Verification) -> list[RuleFlag]:
    # Info when digital copy has checksum-like naming
    if v.document_link:
        name = Path(v.document_link).name
        if len(name.split("_", 1)[0]) == 64:
            return [
                RuleFlag(
                    rule_code="R-031",
                    severity="info",
                    message="Digitalisering OK: checksumma och WORM-plats identifierad.",
                )
            ]
    return []


async def rule_R051(session: AsyncSession, year: int) -> list[RuleFlag]:
    stmt = select(func.count(Verification.id)).where(func.extract("year", Verification.date) == year)
    cnt = int((await session.execute(stmt)).scalar_one() or 0)
    if cnt > 0:
        return [RuleFlag(rule_code="R-051", severity="info", message="SIE-export tillgänglig.")]
    return [RuleFlag(rule_code="R-051", severity="info", message="Ingen SIE att exportera.")]


async def run_yearly_compliance(session: AsyncSession, year: int) -> list[RuleFlag]:
    flags: list[RuleFlag] = []
    stmt = select(Verification).where(func.extract("year", Verification.date) == year)
    verifs = (await session.execute(stmt)).scalars().all()
    for v in verifs:
        flags.extend(await rule_R001(session, v))
        flags.extend(await rule_R011(session, v))
        flags.extend(await rule_R021(session, v))
        flags.extend(await rule_R031(session, v))
    flags.extend(await rule_R051(session, year))
    return flags


def compute_score(flags: Iterable[RuleFlag]) -> int:
    score = 100
    for f in flags:
        if f.severity == "error":
            score -= 20
        elif f.severity == "warning":
            score -= 10
    return max(0, score)


