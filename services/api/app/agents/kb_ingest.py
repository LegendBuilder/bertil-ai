from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import re
try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None  # type: ignore


def _extract_snippets(text: str, url: str, section: str) -> dict:
    # Very light extraction: split by paragraphs and keep top N with simple heuristics
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 0]
    snippets = []
    for p in paras[:20]:
        if len(p) < 200:
            continue
        snippets.append({"url": url, "snippet": p[:500]})
    return {"section": section, "url": url, "snippets": snippets}


def ingest_pages(pages: Iterable[tuple[str, str]], out_dir: str = "kb") -> list[str]:
    """
    Ingest a set of pages into structured JSON files for the RAG KB.

    pages: iterable of (url, raw_text)
    out_dir: output folder for JSON files
    Returns list of written file paths.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for i, (url, text) in enumerate(pages, start=1):
        # Clean HTML if needed
        if "<" in text and ">" in text and BeautifulSoup is not None:
            try:
                soup = BeautifulSoup(text, "html.parser")
                # Drop nav/footer/script/style
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text("\n")
            except Exception:
                pass
        section = re.sub(r"[^a-z0-9]+", "_", url.lower())[:32]
        obj = _extract_snippets(text, url, section)
        path = Path(out_dir) / f"{section}.json"
        prev = path.read_text(encoding="utf-8") if path.exists() else None
        data = json.dumps(obj, ensure_ascii=False, indent=2)
        if prev != data:  # simple diff to avoid churn
            path.write_text(data, encoding="utf-8")
        written.append(str(path))
    return written


