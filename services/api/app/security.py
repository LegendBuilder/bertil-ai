from __future__ import annotations

from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, status
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



