"""Sale observations for monitor/enforce coffee sale tracking.

Revision ID: 007_sale_observations
Revises: 006_promocode_length
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_sale_observations"
down_revision: str | Sequence[str] | None = "006_promocode_length"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sale_observations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("promocode_id", sa.UUID(), nullable=True),
        sa.Column("promocode_value", sa.String(length=20), nullable=True),
        sa.Column("customer_erp_id", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=128), nullable=True),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_kg", sa.Float(), nullable=True),
        sa.Column("qty_pieces", sa.Float(), nullable=True),
        sa.Column("products", sa.Text(), nullable=True),
        sa.Column("group_ids", sa.String(length=128), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("enforcement_mode", sa.String(length=16), nullable=False),
        sa.Column(
            "promocode_closed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["promocode_id"], ["promocodes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_erp_id",
            "order_id",
            name="uq_sale_observations_customer_order",
        ),
    )
    op.create_index(
        "ix_sale_observations_promocode_id",
        "sale_observations",
        ["promocode_id"],
    )
    op.create_index(
        "ix_sale_observations_customer_erp_id",
        "sale_observations",
        ["customer_erp_id"],
    )
    op.create_index("ix_sale_observations_verdict", "sale_observations", ["verdict"])
    op.create_index(
        "ix_sale_observations_detected_at",
        "sale_observations",
        ["detected_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sale_observations_detected_at", table_name="sale_observations")
    op.drop_index("ix_sale_observations_verdict", table_name="sale_observations")
    op.drop_index("ix_sale_observations_customer_erp_id", table_name="sale_observations")
    op.drop_index("ix_sale_observations_promocode_id", table_name="sale_observations")
    op.drop_table("sale_observations")
