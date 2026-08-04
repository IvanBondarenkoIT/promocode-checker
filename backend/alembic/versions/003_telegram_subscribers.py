"""Telegram subscribers and bot poll offset.

Revision ID: 003_telegram_subscribers
Revises: 002_campaigns
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_telegram_subscribers"
down_revision: str | Sequence[str] | None = "002_campaigns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_subscribers",
        sa.Column("chat_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_table(
        "telegram_bot_state",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("update_offset", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute("INSERT INTO telegram_bot_state (id, update_offset) VALUES (1, 0)")


def downgrade() -> None:
    op.drop_table("telegram_bot_state")
    op.drop_table("telegram_subscribers")
