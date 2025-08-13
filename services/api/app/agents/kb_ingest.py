from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import re


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
        section = re.sub(r"[^a-z0-9]+", "_", url.lower())[:32]
        obj = _extract_snippets(text, url, section)
        path = Path(out_dir) / f"{section}.json"
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(path))
    return written


