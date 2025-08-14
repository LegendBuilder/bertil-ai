from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
try:
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:  # pragma: no cover
    Vector = None  # type: ignore


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    personnummer_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    bankid_subject: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    mfa: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orgnr: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    bas_chart_version: Mapped[Optional[str]] = mapped_column(String(20))


class FiscalYear(Base):
    __tablename__ = "fiscal_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    k2_k3: Mapped[Optional[str]] = mapped_column(String(10))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    fiscal_year_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fiscal_years.id"))
    type: Mapped[str] = mapped_column(String(20))
    storage_uri: Mapped[str] = mapped_column(String(500))
    hash_sha256: Mapped[str] = mapped_column(String(64), index=True)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    key: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(500))
    confidence: Mapped[float] = mapped_column(Numeric(5, 2))


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    fiscal_year_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fiscal_years.id"))
    immutable_seq: Mapped[int] = mapped_column(BigInteger, index=True)
    date: Mapped[datetime] = mapped_column(Date)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="SEK")
    vat_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    vat_code: Mapped[Optional[str]] = mapped_column(String(20))
    counterparty: Mapped[Optional[str]] = mapped_column(String(200))
    document_link: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_id: Mapped[int] = mapped_column(ForeignKey("verifications.id"), index=True)
    account: Mapped[str] = mapped_column(String(10))
    debit: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    credit: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    dimension: Mapped[Optional[str]] = mapped_column(String(50))


class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column(Integer)
    rule_code: Mapped[str] = mapped_column(String(10))
    severity: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(String(500))
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100))


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))
    target: Mapped[str] = mapped_column(String(200))
    before_hash: Mapped[Optional[str]] = mapped_column(String(64))
    after_hash: Mapped[Optional[str]] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    signature: Mapped[Optional[str]] = mapped_column(String(128))


class VendorEmbedding(Base):
    __tablename__ = "vendor_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    # Use pgvector's Vector type if available; fall back to String to avoid import-time errors
    if Vector:
        embedding = mapped_column(Vector(16))  # type: ignore[assignment]
    else:  # pragma: no cover
        embedding: Mapped[str] = mapped_column(String(400))
    suggested_account: Mapped[str | None] = mapped_column(String(10))
    vat_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))


class VatCode(Base):
    __tablename__ = "vat_codes"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str] = mapped_column(String(200))
    rate: Mapped[float] = mapped_column(Numeric(5, 2))
    reverse_charge: Mapped[bool] = mapped_column()


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, index=True, default=1)
    import_batch_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date: Mapped[datetime] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="SEK")
    description: Mapped[str] = mapped_column(String(500))
    counterparty_ref: Mapped[str | None] = mapped_column(String(200))
    matched_verification_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PeriodLock(Base):
    __tablename__ = "period_locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, index=True)
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, index=True)
    type: Mapped[str] = mapped_column(String(40))  # e.g., autopost|settle|vat
    payload_json: Mapped[str] = mapped_column(Text)  # JSON payload
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|done|cancelled
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IntegrationToken(Base):
    __tablename__ = "integration_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(40))  # e.g., fortnox
    access_token: Mapped[str] = mapped_column(String(500))
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500))
    scope: Mapped[Optional[str]] = mapped_column(String(200))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    orgnr: Mapped[Optional[str]] = mapped_column(String(20))  # Swedish org number
    vat_number: Mapped[Optional[str]] = mapped_column(String(30))  # EU VAT number
    email: Mapped[Optional[str]] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(2), default="SE")  # ISO country code
    payment_terms: Mapped[int] = mapped_column(Integer, default=30)  # days
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), index=True)  # Sequential number
    invoice_date: Mapped[datetime] = mapped_column(Date)
    due_date: Mapped[datetime] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="SEK")
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2))  # Amount before VAT
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2))  # Amount including VAT
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|sent|paid|overdue|cancelled
    notes: Mapped[Optional[str]] = mapped_column(Text)
    pdf_uri: Mapped[Optional[str]] = mapped_column(String(500))  # S3 URI for generated PDF
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_id: Mapped[Optional[int]] = mapped_column(ForeignKey("verifications.id"))  # When paid
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship("InvoiceLineItem", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Numeric(10, 3), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2))
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2))  # 25.0 for 25%
    vat_code: Mapped[Optional[str]] = mapped_column(String(20))  # SE25, SE12, SE06
    line_total: Mapped[float] = mapped_column(Numeric(14, 2))  # quantity * unit_price
    line_vat: Mapped[float] = mapped_column(Numeric(14, 2))  # VAT amount for this line
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="line_items")


class InvoiceSequence(Base):
    __tablename__ = "invoice_sequences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), unique=True, index=True)
    current_number: Mapped[int] = mapped_column(Integer, default=0)
    prefix: Mapped[str] = mapped_column(String(10), default="2024")  # Year prefix
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

