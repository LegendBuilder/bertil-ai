from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Verification, ComplianceFlag, Entry, FiscalYear


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
    # Support app-style link "/documents/{id}" or filesystem path
    link = v.document_link
    if link.startswith("/documents/"):
        digest = link.split("/documents/")[-1]
        # locate file in .worm_store similar to ingest layout
        store_dir = Path(".worm_store") / digest[:2] / digest[2:4]
        found = False
        if store_dir.exists():
            for p in store_dir.iterdir():
                if p.is_file() and p.name.startswith(f"{digest}_"):
                    found = True
                    break
        if not found:
            return [
                RuleFlag(
                    rule_code="R-021",
                    severity="error",
                    message="Underlag hittas ej i WORM-lagring.",
                )
            ]
    else:
        p = Path(link)
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


async def rule_DUP(session: AsyncSession, v: Verification) -> list[RuleFlag]:
    # Duplicate detector: same document_link used in another verification
    if not v.document_link:
        return []
    stmt = (
        select(Verification)
        .where(Verification.document_link == v.document_link)
        .where(Verification.id != v.id)
        .limit(1)
    )
    other = (await session.execute(stmt)).scalars().first()
    if other:
        return [
            RuleFlag(
                rule_code="R-DUP",
                severity="warning",
                message="Dubblett: underlag används redan i annan verifikation.",
            )
        ]
    return []


async def rule_RVAT(session: AsyncSession, v: Verification) -> list[RuleFlag]:
    # VAT plausibility vs total amount using entries on 264x
    estmt = select(Entry).where(Entry.verification_id == v.id)
    entries = (await session.execute(estmt)).scalars().all()
    vat = sum(float(e.debit or 0.0) for e in entries if e.account.startswith("264"))
    total = float(v.total_amount or 0.0)
    if total <= 0 or vat <= 0:
        return []
    ratio = vat / total
    expected = [0.25 / 1.25, 0.12 / 1.12, 0.06 / 1.06]
    if not any(abs(ratio - r) < 0.03 for r in expected):
        return [
            RuleFlag(
                rule_code="R-VAT",
                severity="warning",
                message="Orimlig moms i relation till totalbelopp.",
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
        flags.extend(await rule_DUP(session, v))
        flags.extend(await rule_RVAT(session, v))
        flags.extend(await rule_PERIOD(session, v))
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


async def run_verification_rules(session: AsyncSession, v: Verification) -> list[RuleFlag]:
    flags: list[RuleFlag] = []
    flags.extend(await rule_R001(session, v))
    flags.extend(await rule_R011(session, v))
    flags.extend(await rule_R021(session, v))
    flags.extend(await rule_R031(session, v))
    flags.extend(await rule_DUP(session, v))
    flags.extend(await rule_RVAT(session, v))
    flags.extend(await rule_PERIOD(session, v))
    return flags


async def rule_PERIOD(session: AsyncSession, v: Verification) -> list[RuleFlag]:
    # Warn if verification date is outside any known fiscal year for org
    if not isinstance(v.date, date):
        return []
    stmt = select(FiscalYear).where(
        FiscalYear.org_id == v.org_id,
        FiscalYear.start_date <= v.date,
        FiscalYear.end_date >= v.date,
    )
    fy = (await session.execute(stmt)).scalars().first()
    if fy is None:
        return [
            RuleFlag(
                rule_code="R-PERIOD",
                severity="warning",
                message="Datum ligger utanför känd bokföringsperiod.",
            )
        ]
    return []


async def persist_flags(session: AsyncSession, entity_type: str, entity_id: int, flags: Iterable[RuleFlag]) -> None:
    for f in flags:
        session.add(
            ComplianceFlag(
                entity_type=entity_type,
                entity_id=entity_id,
                rule_code=f.rule_code,
                severity=f.severity,
                message=f.message,
                resolved_by=None,
            )
        )
    await session.commit()

