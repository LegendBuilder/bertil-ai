from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20250820_000002_ai_feedback"
down_revision = "20250815_000001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("vendor", sa.String(200), nullable=False),
        sa.Column("vendor_ilike", sa.String(200), index=True, nullable=False),
        sa.Column("correct_account", sa.String(10)),
        sa.Column("correct_vat_code", sa.String(20)),
        sa.Column("correct_vat_rate", sa.Numeric(5, 2)),
        sa.Column("org_id", sa.Integer()),
        sa.Column("verification_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_feedback")





