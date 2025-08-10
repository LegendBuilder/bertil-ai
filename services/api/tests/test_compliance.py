from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.app.models import Verification, Entry
from services.api.app.db import SessionLocal, engine, Base
from services.api.app.compliance import run_verification_rules


@pytest.mark.asyncio
async def test_r001_missing_fields(tmp_path):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:  # type: AsyncSession
        v = Verification(org_id=1, immutable_seq=1, date=date.today(), total_amount=123.45, currency="SEK")
        session.add(v)
        await session.flush()
        # Missing counterparty, vat_amount, document_link
        flags = await run_verification_rules(session, v)
        codes = {f.rule_code for f in flags}
        assert "R-001" in codes


@pytest.mark.asyncio
async def test_r011_timeliness_warning():
    async with SessionLocal() as session:  # type: AsyncSession
        v = Verification(org_id=1, immutable_seq=2, date=date.today() - timedelta(days=45), total_amount=100, currency="SEK", vat_amount=0, counterparty="X", document_link="/documents/abc")
        session.add(v)
        await session.flush()
        flags = await run_verification_rules(session, v)
        codes = {f.rule_code for f in flags}
        assert "R-011" in codes


@pytest.mark.asyncio
async def test_rvat_plausibility():
    async with SessionLocal() as session:  # type: AsyncSession
        v = Verification(org_id=1, immutable_seq=3, date=date.today(), total_amount=125.00, currency="SEK", vat_amount=25.00, counterparty="Cafe", document_link="/documents/def")
        session.add(v)
        await session.flush()
        session.add_all([
            Entry(verification_id=v.id, account="5811", debit=100.0, credit=0.0),
            Entry(verification_id=v.id, account="2641", debit=25.0, credit=0.0),
            Entry(verification_id=v.id, account="1910", debit=0.0, credit=125.0),
        ])
        await session.flush()
        flags = await run_verification_rules(session, v)
        # Should not warn for VAT plausibility
        codes = {f.rule_code for f in flags}
        assert "R-VAT" not in codes


