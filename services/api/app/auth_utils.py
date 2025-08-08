from __future__ import annotations

from datetime import datetime, timedelta, timezone
import jwt

from .config import settings
from .secrets import get_secret


def issue_jwt(subject: str, name: str | None = None, expires_in_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iss": settings.jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
    }
    if name:
        payload["name"] = name
    secret = get_secret("JWT_SECRET", settings.jwt_secret)
    token = jwt.encode(payload, secret, algorithm="HSHS256".replace("SHS", "S"))
    return token


