from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20250825_000003_rbac_bank_tokens_review"
down_revision = "20250820_000002_ai_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add org_id to bank_transactions (default 1 for existing)
    with op.batch_alter_table("bank_transactions") as batch:
        batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))
        batch.create_index("ix_bank_transactions_org_id", ["org_id"], unique=False)
    # Backfill org_id to 1 for existing rows where null
    try:
        op.execute("UPDATE bank_transactions SET org_id = 1 WHERE org_id IS NULL")
    except Exception:
        pass
    with op.batch_alter_table("bank_transactions") as batch:
        batch.alter_column("org_id", nullable=False, existing_type=sa.Integer())

    # Create review_tasks and integration_tokens tables if not yet present (defensive)
    # review_tasks
    try:
        op.create_table(
            "review_tasks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.Integer(), index=True, nullable=False),
            sa.Column("type", sa.String(40), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("confidence", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.0")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
    except Exception:
        pass

    # integration_tokens
    try:
        op.create_table(
            "integration_tokens",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.Integer(), index=True, nullable=False),
            sa.Column("provider", sa.String(40), nullable=False),
            sa.Column("access_token", sa.String(500), nullable=False),
            sa.Column("refresh_token", sa.String(500)),
            sa.Column("scope", sa.String(200)),
            sa.Column("expires_at", sa.DateTime()),
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_table("integration_tokens")
    except Exception:
        pass
    try:
        op.drop_table("review_tasks")
    except Exception:
        pass
    with op.batch_alter_table("bank_transactions") as batch:
        try:
            batch.drop_index("ix_bank_transactions_org_id")
        except Exception:
            pass
        try:
            batch.drop_column("org_id")
        except Exception:
            pass


