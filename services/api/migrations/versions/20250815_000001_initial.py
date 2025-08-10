from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20250815_000001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension when available (Postgres)
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except Exception:
        pass
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("personnummer_hash", sa.String(128)),
        sa.Column("bankid_subject", sa.String(128), index=True),
        sa.Column("name", sa.String(200)),
        sa.Column("email", sa.String(200)),
        sa.Column("mfa", sa.String(50)),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orgnr", sa.String(20), unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(300)),
        sa.Column("bas_chart_version", sa.String(20)),
    )
    op.create_table(
        "fiscal_years",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id")),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("k2_k3", sa.String(10)),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id")),
        sa.Column("fiscal_year_id", sa.Integer(), sa.ForeignKey("fiscal_years.id")),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("storage_uri", sa.String(500), nullable=False),
        sa.Column("hash_sha256", sa.String(64), index=True),
        sa.Column("ocr_text", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), index=True),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2)),
    )
    op.create_table(
        "verifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), index=True),
        sa.Column("fiscal_year_id", sa.Integer(), sa.ForeignKey("fiscal_years.id")),
        sa.Column("immutable_seq", sa.BigInteger(), index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="SEK"),
        sa.Column("vat_amount", sa.Numeric(14, 2)),
        sa.Column("vat_code", sa.String(20)),
        sa.Column("counterparty", sa.String(200)),
        sa.Column("document_link", sa.String(500)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("verification_id", sa.Integer(), sa.ForeignKey("verifications.id"), index=True),
        sa.Column("account", sa.String(10), nullable=False),
        sa.Column("debit", sa.Numeric(14, 2)),
        sa.Column("credit", sa.Numeric(14, 2)),
        sa.Column("dimension", sa.String(50)),
    )
    op.create_table(
        "compliance_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("rule_code", sa.String(10), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("resolved_by", sa.String(100)),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target", sa.String(200), nullable=False),
        sa.Column("before_hash", sa.String(64)),
        sa.Column("after_hash", sa.String(64)),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("signature", sa.String(128)),
    )

    # Vendor embeddings (optional)
    try:
        op.create_table(
            "vendor_embeddings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(200), unique=True, index=True),
            sa.Column("embedding", sa.dialects.postgresql.ARRAY(sa.Float())),
            sa.Column("suggested_account", sa.String(10)),
            sa.Column("vat_rate", sa.Numeric(5, 2)),
        )
    except Exception:
        # Fallback for DBs without pgvector/ARRAY: store as json string
        op.create_table(
            "vendor_embeddings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(200), unique=True, index=True),
            sa.Column("embedding", sa.String(2000)),
            sa.Column("suggested_account", sa.String(10)),
            sa.Column("vat_rate", sa.Numeric(5, 2)),
        )

    # Bank transactions
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("import_batch_id", sa.Integer()),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="SEK"),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("counterparty_ref", sa.String(200)),
        sa.Column("matched_verification_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # VAT codes
    op.create_table(
        "vat_codes",
        sa.Column("code", sa.String(20), primary_key=True),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("reverse_charge", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    for t in [
        "vendor_embeddings",
        "audit_log",
        "compliance_flags",
        "entries",
        "verifications",
        "extracted_fields",
        "documents",
        "fiscal_years",
        "organizations",
        "users",
    ]:
        op.drop_table(t)


