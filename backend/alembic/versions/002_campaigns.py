"""Add campaigns table and promocodes.campaign_id.

Revision ID: 002_campaigns
Revises: 001_initial_schema
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_campaigns"
down_revision: str | Sequence[str] | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

campaign_status = postgresql.ENUM(
    "DRAFT",
    "ACTIVE",
    "CLOSED",
    name="campaign_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    campaign_status.create(bind, checkfirst=True)

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("status", campaign_status, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_campaigns_code", "campaigns", ["code"], unique=True)
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    op.add_column(
        "promocodes",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_promocodes_campaign_id_campaigns",
        "promocodes",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_promocodes_campaign_id", "promocodes", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_promocodes_campaign_id", table_name="promocodes")
    op.drop_constraint("fk_promocodes_campaign_id_campaigns", "promocodes", type_="foreignkey")
    op.drop_column("promocodes", "campaign_id")
    op.drop_index("ix_campaigns_status", table_name="campaigns")
    op.drop_index("ix_campaigns_code", table_name="campaigns")
    op.drop_table("campaigns")
    bind = op.get_bind()
    campaign_status.drop(bind, checkfirst=True)
