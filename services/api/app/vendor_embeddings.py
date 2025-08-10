from __future__ import annotations

from typing import List, Tuple
from .config import settings

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:  # pragma: no cover
    Vector = object  # fallback type for import time


def embed_vendor_name(name: str) -> List[float]:
    if settings.embeddings_provider == "minilm":
        try:
            # Lazy import to avoid heavy deps by default
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("MiniLM not installed. Set embeddings_provider=stub or install sentence-transformers.") from exc
        # Cache the model at module level
        global _model
        try:
            _model  # type: ignore[name-defined]
        except NameError:
            _model = SentenceTransformer("all-MiniLM-L6-v2")  # type: ignore[assignment]
        vec = _model.encode([name])[0]
        # Truncate/pad to 16 dims for DB schema simplicity
        import numpy as np  # type: ignore
        v = np.array(vec, dtype=float)
        if v.shape[0] >= 16:
            v16 = v[:16]
        else:
            v16 = np.pad(v, (0, 16 - v.shape[0]))
        n = float(np.linalg.norm(v16) or 1.0)
        return [float(x / n) for x in v16]
    # Stub: deterministic 16-dim embedding
    import math
    vec = [0.0] * 16
    for i, ch in enumerate(name.lower().encode("utf-8")):
        vec[i % 16] += (ch % 31) / 31.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]



