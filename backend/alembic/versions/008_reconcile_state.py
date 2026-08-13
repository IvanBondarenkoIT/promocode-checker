"""Persistent ERP reconcile observe cursor.

Revision ID: 008_reconcile_state
Revises: 007_sale_observations
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_reconcile_state"
down_revision: str | Sequence[str] | None = "007_sale_observations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reconcile_state",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("last_scan_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_erp_rows", sa.Integer(), nullable=True),
        sa.Column("last_erp_ms", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute("INSERT INTO reconcile_state (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("reconcile_state")
