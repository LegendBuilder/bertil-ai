from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class AiFeedback(Base):
    __tablename__ = "ai_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Free text vendor as entered/displayed; we also store lowercase for simple lookup
    vendor: Mapped[str] = mapped_column(String(200))
    vendor_ilike: Mapped[str] = mapped_column(String(200), index=True)
    # What user corrected
    correct_account: Mapped[Optional[str]] = mapped_column(String(10))
    correct_vat_code: Mapped[Optional[str]] = mapped_column(String(20))
    correct_vat_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    # Light context
    org_id: Mapped[Optional[int]] = mapped_column(Integer)
    verification_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





