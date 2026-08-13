"""Per-subscriber Telegram alert topics.

Revision ID: 009_telegram_topics
Revises: 008_reconcile_state
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_telegram_topics"
down_revision: str | Sequence[str] | None = "008_reconcile_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FULL_TOPICS = "scans,closures,sales,fraud,digest,system"
DIGEST_TOPICS = "digest,system"


def upgrade() -> None:
    op.add_column(
        "telegram_subscribers",
        sa.Column(
            "topics",
            sa.String(length=255),
            nullable=False,
            server_default=FULL_TOPICS,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE telegram_subscribers "
            f"SET topics = '{DIGEST_TOPICS}' "
            "WHERE alert_mode = 'digest'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE telegram_subscribers "
            f"SET topics = '{FULL_TOPICS}' "
            "WHERE alert_mode IS DISTINCT FROM 'digest'"
        )
    )


def downgrade() -> None:
    op.drop_column("telegram_subscribers", "topics")
