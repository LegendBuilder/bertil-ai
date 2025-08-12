from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_session
from ..security import require_user, enforce_rate_limit
from ..config import settings
from ..models import Document


router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/worm/{doc_id}")
async def worm_status(doc_id: str, session: AsyncSession = Depends(get_session), user=Depends(require_user), _rl: None = Depends(enforce_rate_limit)) -> dict:
    d = (await session.execute(select(Document).where(Document.hash_sha256 == doc_id))).scalars().first()
    if not d:
        raise HTTPException(status_code=404, detail="document not found")
    uri = d.storage_uri or ""
    if uri.startswith("s3://"):
        if not settings.aws_region or not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise HTTPException(status_code=501, detail="aws not configured")
        try:
            import boto3  # type: ignore
            s3uri = uri[5:]
            bucket, key = s3uri.split("/", 1)
            s3 = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            lock_cfg = s3.get_object_lock_configuration(Bucket=bucket)
            try:
                retention = s3.get_object_retention(Bucket=bucket, Key=key)
            except Exception:
                retention = {"Retention": None}
            head = s3.head_object(Bucket=bucket, Key=key)
            legal_hold = head.get("ObjectLockLegalHoldStatus")
            return {
                "backend": "s3",
                "bucket": bucket,
                "key": key,
                "object_lock": lock_cfg.get("ObjectLockConfiguration"),
                "retention": retention.get("Retention"),
                "legal_hold": legal_hold,
            }
        except Exception as e:  # pragma: no cover - requires AWS
            raise HTTPException(status_code=502, detail=f"s3 error: {e}")
    elif uri.startswith("http"):
        # Supabase or other HTTP storage
        return {
            "backend": "supabase",
            "public": bool(settings.supabase_storage_public),
            "signed_url": not settings.supabase_storage_public,
        }
    else:
        # Local WORM-like store
        return {"backend": "local", "path": uri}


@router.get("/worm/bucket/status")
async def worm_bucket_status(user=Depends(require_user)) -> dict:
    """Report S3 bucket Object Lock / region policy when configured."""
    if not settings.s3_bucket:
        return {"backend": "local/dev", "object_lock": None}
    if not (settings.aws_region and settings.aws_access_key_id and settings.aws_secret_access_key):
        raise HTTPException(status_code=501, detail="aws not configured")
    try:
        import boto3  # type: ignore
        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        lock_cfg = s3.get_object_lock_configuration(Bucket=settings.s3_bucket)
        bucket_loc = s3.get_bucket_location(Bucket=settings.s3_bucket)
        return {
            "backend": "s3",
            "bucket": settings.s3_bucket,
            "object_lock": lock_cfg.get("ObjectLockConfiguration"),
            "region": bucket_loc.get("LocationConstraint"),
        }
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"s3 error: {e}")













