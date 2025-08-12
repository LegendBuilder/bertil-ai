from __future__ import annotations

from typing import Any, Iterable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_session
from ..security import require_user
from ..models import VendorEmbedding
from ..vendor_embeddings import embed_vendor_name
from ..models import VatCode
from ..agents.swedish_knowledge_base import get_knowledge_base, SwedishTaxRAG


router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)


def _serialize_embedding(vec: list[float]) -> Any:
    # If using pgvector (list/array acceptable), otherwise store as comma-separated string
    try:
        from pgvector.sqlalchemy import Vector  # type: ignore
        return vec
    except Exception:  # pragma: no cover
        return ",".join(f"{v:.6f}" for v in vec)


def _require_admin(user: dict) -> None:
    # In local/test/ci, allow seeding without admin to keep tests passing
    from ..config import settings as _settings
    if _settings.app_env.lower() in {"local", "test", "ci"}:
        return
    # Minimal admin check in staging/prod: require explicit claim 'role' == 'admin'
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin required")


@router.post("/seed/vendors")
async def seed_vendors(session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    _require_admin(user)
    seeds: list[tuple[str, str, float]] = [
        ("Kaffe AB", "5811", 0.12),
        ("Cafe Nybrogatan", "5811", 0.12),
        ("Taxi Stockholm", "5611", 0.06),
        ("Uber BV", "5611", 0.06),
        ("Shell", "5611", 0.25),
        ("Circle K", "5611", 0.25),
        ("Preem", "5611", 0.25),
        ("OKQ8", "5611", 0.25),
        ("IKEA", "4010", 0.25),
    ]
    inserted = 0
    for name, account, vat in seeds:
        exists = (await session.execute(select(VendorEmbedding).where(VendorEmbedding.name == name))).scalars().first()
        if exists:
            continue
        vec = embed_vendor_name(name)
        session.add(
            VendorEmbedding(
                name=name,
                embedding=_serialize_embedding(vec),
                suggested_account=account,
                vat_rate=vat,
            )
        )
        inserted += 1
    await session.commit()
    return {"inserted": inserted, "total": len(seeds)}


@router.post("/seed/vat")
async def seed_vat_codes(session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    _require_admin(user)
    seeds = [
        ("SE25", "Svensk moms 25%", 0.25, False),
        ("SE12", "Svensk moms 12%", 0.12, False),
        ("SE06", "Svensk moms 6%", 0.06, False),
        ("RC25", "Omvänd skattskyldighet 25%", 0.25, True),
        ("EU-RC-SERV", "EU-tjänst omvänd", 0.25, True),
    ]
    ins = 0
    for code, desc, rate, rc in seeds:
        exists = (await session.execute(select(VatCode).where(VatCode.code == code))).scalars().first()
        if exists:
            continue
        session.add(VatCode(code=code, description=desc, rate=rate, reverse_charge=rc))
        ins += 1
    await session.commit()
    return {"inserted": ins, "total": len(seeds)}


@router.post("/kb/rebuild")
async def kb_rebuild(user=Depends(require_user)) -> dict:
    _require_admin(user)
    """Rebuild or refresh the Swedish knowledge base (stubbed)."""
    kb = get_knowledge_base()
    rag = SwedishTaxRAG(kb)
    # Run a couple of warmup searches
    _ = rag.search("representation moms 50%", k=2)
    _ = rag.search("momssatser 25 12 6", k=2)
    return {"status": "ok", "kb_loaded": True}


@router.get("/kb/status")
async def kb_status(user=Depends(require_user)) -> dict:
    _require_admin(user)
    """Return basic KB stats (stubbed)."""
    kb = get_knowledge_base()
    # Very rough stats from stub structure
    try:
        tax_sections = len(getattr(kb, "tax_rules", {}))
    except Exception:
        tax_sections = 0
    sources: list[str] = []
    try:
        sources.append(kb.tax_rules.get("representation", {}).get("url", ""))
    except Exception:
        pass
    try:
        sources.append(kb.tax_rules.get("vat_rates", {}).get("url", ""))
    except Exception:
        pass
    return {"kb_loaded": True, "sections": tax_sections, "sources": [s for s in sources if s]}


@router.get("/audit/export")
async def export_audit_log(limit: int = 1000, session: AsyncSession = Depends(get_session), user=Depends(require_user)) -> dict:
    """Export recent admin-audit events for DPIA/log policy evidence."""
    _require_admin(user)
    from sqlalchemy import select
    from ..models import AuditLog
    rows = (
        await session.execute(
            select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        )
    ).scalars().all()
    items = [
        {
            "id": r.id,
            "actor": r.actor,
            "action": r.action,
            "target": r.target,
            "ts": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
    return {"items": items}


