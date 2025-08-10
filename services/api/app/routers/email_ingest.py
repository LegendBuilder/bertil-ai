from __future__ import annotations

import email
import hashlib
from email.message import Message
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..config import settings
from .ingest import upload_document
from fastapi import UploadFile
from io import BytesIO


router = APIRouter(prefix="/email", tags=["ingest"])


def _iter_stub_emails() -> List[tuple[str, bytes]]:
    inbox = Path(".email_ingest_inbox")
    if not inbox.exists():
        return []
    items: List[tuple[str, bytes]] = []
    for p in inbox.glob("*.eml"):
        items.append((p.name, p.read_bytes()))
    return items


@router.post("/ingest")
async def ingest_emails(session: AsyncSession = Depends(get_session)) -> dict:
    if not settings.email_ingest_enabled:
        raise HTTPException(status_code=501, detail="email ingest disabled")
    processed = 0
    messages: List[tuple[str, bytes]]
    # For now, stub: read .eml files from local folder. Real IMAP behind flag later.
    messages = _iter_stub_emails()
    for fname, raw in messages:
        try:
            msg: Message = email.message_from_bytes(raw)
            # Sender rules
            sender = (msg.get('From') or '').lower()
            meta = {}
            try:
                import json as _json
                rules = _json.loads(settings.email_sender_rules_json or "{}")
                for k, v in rules.items():
                    if k.lower() in sender:
                        meta.update(v)
            except Exception:
                pass
            # Extract first attachment that looks like an image/pdf
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename() or "attachment.bin"
                    content = part.get_payload(decode=True) or b""
                    # Reuse upload endpoint logic by constructing UploadFile-like object
                    uf = UploadFile(filename=filename, file=BytesIO(content), headers={})
                    import json as _json
                    meta_json = _json.dumps(meta)
                    await upload_document(file=uf, meta_json=meta_json, session=session)
                    processed += 1
                    break
        except Exception:
            continue
    return {"processed": processed}


@router.post("/ingest/imap")
async def ingest_emails_imap(session: AsyncSession = Depends(get_session)) -> dict:
    if not settings.email_ingest_enabled:
        raise HTTPException(status_code=501, detail="email ingest disabled")
    if not settings.email_imap_host or not settings.email_imap_user or not settings.email_imap_password:
        raise HTTPException(status_code=400, detail="imap config missing")
    import imaplib
    processed = 0
    M = imaplib.IMAP4_SSL(settings.email_imap_host, settings.email_imap_port)
    try:
        M.login(settings.email_imap_user, settings.email_imap_password)
        M.select('INBOX')
        typ, data = M.search(None, 'UNSEEN')
        if typ != 'OK':
            return {"processed": 0}
        for num in data[0].split():
            typ, msg_data = M.fetch(num, '(RFC822)')
            if typ != 'OK' or not msg_data:
                continue
            raw = msg_data[0][1]
            try:
                msg: Message = email.message_from_bytes(raw)
                sender = (msg.get('From') or '').lower()
                meta = {}
                try:
                    import json as _json
                    rules = _json.loads(settings.email_sender_rules_json or "{}")
                    for k, v in rules.items():
                        if k.lower() in sender:
                            meta.update(v)
                except Exception:
                    pass
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename() or 'attachment.bin'
                        content = part.get_payload(decode=True) or b''
                        uf = UploadFile(filename=filename, file=BytesIO(content), headers={})
                        import json as _json
                        meta_json = _json.dumps(meta)
                        await upload_document(file=uf, meta_json=meta_json, session=session)
                        processed += 1
                        break
                # mark seen
                M.store(num, '+FLAGS', '\\Seen')
            except Exception:
                continue
    finally:
        try:
            M.logout()
        except Exception:
            pass
    return {"processed": processed}


