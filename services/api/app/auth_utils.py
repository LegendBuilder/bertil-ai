from __future__ import annotations

from datetime import datetime, timedelta, timezone
import jwt

from .config import settings


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
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token


