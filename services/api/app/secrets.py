from __future__ import annotations

import os
from typing import Optional

from .config import settings


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    # 1) ENV direct
    if name in os.environ:
        return os.environ.get(name)

    # 2) Settings fallback for known names
    if name == "JWT_SECRET" and settings.jwt_secret:
        return settings.jwt_secret

    # 3) Local file store ./.secrets/{name}
    try:
        path = os.path.join(".secrets", name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass

    # 4) AWS Secrets Manager (optional)
    try:
        secret_name = os.environ.get("AWS_SECRET_NAME")
        if secret_name and name == "JWT_SECRET":
            import boto3  # type: ignore

            client = boto3.client("secretsmanager", region_name=settings.aws_region)
            resp = client.get_secret_value(SecretId=secret_name)
            val = resp.get("SecretString")
            if val:
                # expect JSON like {"JWT_SECRET":"..."}
                import json

                data = json.loads(val)
                return data.get(name) or default
    except Exception:
        # fall through
        pass

    return default


