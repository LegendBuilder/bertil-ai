from __future__ import annotations

from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from .config import settings
from .secrets import get_secret


# HTTP Bearer token extractor. auto_error=False to allow optional auth in local/test.
bearer_scheme = HTTPBearer(auto_error=False)


def _decode_jwt(token: str) -> Dict[str, Any]:
    secret = get_secret("JWT_SECRET", settings.jwt_secret) or ""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "exp", "iat"]})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    iss = payload.get("iss")
    if iss and iss != settings.jwt_issuer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid issuer")
    return payload


async def require_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)]
) -> Dict[str, Any]:
    """Require a valid user when not in local/test environments.

    In local/test/ci, returns a stub user if no token is provided to keep developer ergonomics
    and avoid breaking tests. In staging/prod, an absent or invalid token results in 401.
    """
    # Local/test environments: allow anonymous with stub identity
    if settings.app_env.lower() in {"local", "test", "ci"}:
        if credentials and credentials.credentials:
            return _decode_jwt(credentials.credentials)
        return {"sub": "local-dev", "iss": settings.jwt_issuer}

    # Staging/prod: enforce bearer token
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    return _decode_jwt(credentials.credentials)


def require_org(user: Dict[str, Any], org_id: int) -> None:
    """Ensure user has access to the given organization.

    Minimal policy: allow if token has matching `org_id` or list `orgs` containing it.
    In local/test/ci, allow all orgs by default for developer ergonomics.
    """
    if settings.app_env.lower() in {"local", "test", "ci"}:
        return
    claim_org = user.get("org_id")
    claim_orgs = user.get("orgs") or []
    if claim_org == org_id or (isinstance(claim_orgs, list) and org_id in claim_orgs):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden for organization")


class RateLimiter:
    """Very simple in-process rate limiter keyed by client IP and path.

    For production, prefer an API gateway/WAF or Redis-based limiter.
    """

    def __init__(self, max_per_minute: int) -> None:
        self.max = max_per_minute
        self._buckets: Dict[str, list[float]] = {}

    def allow(self, key: str, now: float) -> bool:
        from time import time as _time
        window_start = now - 60.0
        bucket = self._buckets.setdefault(key, [])
        # drop old
        i = 0
        for i in range(len(bucket)):
            if bucket[i] >= window_start:
                break
        if i > 0:
            del bucket[:i]
        if len(bucket) >= self.max:
            return False
        bucket.append(now)
        return True


_rate_limiter: RateLimiter | None = None


async def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency to enforce naive per-IP rate limit.

    Disabled if settings.rate_limit_enabled is False.
    """
    from time import time as _time
    if not settings.rate_limit_enabled:
        return
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_per_minute=settings.rate_limit_per_minute)
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"
    if not _rate_limiter.allow(key, _time()):
        raise HTTPException(status_code=429, detail="rate limit exceeded")



