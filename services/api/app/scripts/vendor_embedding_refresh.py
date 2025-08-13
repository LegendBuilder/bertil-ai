from __future__ import annotations

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update

from ..config import settings
from ..models import VendorEmbedding
from ..vendor_embeddings import embed_vendor_name


async def main() -> None:
    engine = create_async_engine(settings.database_url, future=True, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        rows = (await session.execute(select(VendorEmbedding))).scalars().all()
        updated = 0
        for r in rows:
            try:
                vec = embed_vendor_name(r.name)
            except Exception:
                continue
            # Store as comma-separated if pgvector not available
            try:
                r.embedding = vec  # type: ignore[assignment]
            except Exception:
                r.embedding = ",".join(f"{v:.6f}" for v in vec)  # type: ignore[assignment]
            updated += 1
        await session.commit()
        print({"updated": updated})


if __name__ == "__main__":
    asyncio.run(main())


