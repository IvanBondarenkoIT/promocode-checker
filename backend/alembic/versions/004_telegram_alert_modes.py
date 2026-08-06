"""Telegram alert modes and digest schedule state.

Revision ID: 004_telegram_alert_modes
Revises: 003_telegram_subscribers
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_telegram_alert_modes"
down_revision: str | Sequence[str] | None = "003_telegram_subscribers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "telegram_subscribers",
        sa.Column(
            "alert_mode",
            sa.String(length=16),
            nullable=False,
            server_default="full",
        ),
    )
    op.create_table(
        "telegram_digest_state",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("last_day_start_on", sa.Date(), nullable=True),
        sa.Column("last_eod_on", sa.Date(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute("INSERT INTO telegram_digest_state (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("telegram_digest_state")
    op.drop_column("telegram_subscribers", "alert_mode")
