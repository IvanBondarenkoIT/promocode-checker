"""Telegram subscriber username/display_name for ops list.

Revision ID: 010_telegram_subscriber_profile
Revises: 009_telegram_topics
Create Date: 2026-08-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_telegram_subscriber_profile"
down_revision: str | Sequence[str] | None = "009_telegram_topics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "telegram_subscribers",
        sa.Column("username", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "telegram_subscribers",
        sa.Column("display_name", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("telegram_subscribers", "display_name")
    op.drop_column("telegram_subscribers", "username")
