from __future__ import annotations

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from ..config import settings
from ..models import VendorEmbedding
from ..models_feedback import AiFeedback
from ..vendor_embeddings import embed_vendor_name


async def main() -> None:
    engine = create_async_engine(settings.database_url, future=True, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # Fold latest feedback into suggested_account/vat_rate and ensure an embedding exists
        fbs = (await session.execute(select(AiFeedback).order_by(AiFeedback.id.desc()).limit(100))).scalars().all()
        upserts = 0
        for fb in fbs:
            if not fb.vendor:
                continue
            row = (await session.execute(select(VendorEmbedding).where(VendorEmbedding.name == fb.vendor))).scalars().first()
            if row is None:
                row = VendorEmbedding(name=fb.vendor, suggested_account=fb.correct_account or None, vat_rate=fb.correct_vat_rate)
                try:
                    row.embedding = embed_vendor_name(fb.vendor)  # type: ignore[assignment]
                except Exception:
                    row.embedding = ",".join(f"{v:.6f}" for v in embed_vendor_name(fb.vendor))  # type: ignore[assignment]
                session.add(row)
                upserts += 1
            else:
                if fb.correct_account:
                    row.suggested_account = fb.correct_account
                if fb.correct_vat_rate is not None:
                    row.vat_rate = fb.correct_vat_rate
        await session.commit()
        print({"upserts": upserts})


if __name__ == "__main__":
    asyncio.run(main())


