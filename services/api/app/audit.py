from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog


async def append_audit_event(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    target: str,
    event_payload_hash: str,
) -> str:
    """Append an audit event and extend the hash chain.

    Chain rule: after_hash = sha256((before_hash or "") + event_payload_hash)
    """
    prev_stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
    prev = (await session.execute(prev_stmt)).scalars().first()
    before_hash: Optional[str] = prev.after_hash if prev else None
    chain_material = (before_hash or "") + event_payload_hash
    after_hash = hashlib.sha256(chain_material.encode("utf-8")).hexdigest()

    audit = AuditLog(
        actor=actor,
        action=action,
        target=target,
        before_hash=before_hash,
        after_hash=after_hash,
        signature=None,
    )
    session.add(audit)
    await session.flush()
    return after_hash


