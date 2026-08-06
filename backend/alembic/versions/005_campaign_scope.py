"""Campaign kind/prefix, customer fields on promocodes, app settings.

Revision ID: 005_campaign_scope
Revises: 004_telegram_alert_modes
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_campaign_scope"
down_revision: str | Sequence[str] | None = "004_telegram_alert_modes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CAMPAIGN_KIND = sa.Enum("TEST", "LIVE", name="campaign_kind")


def upgrade() -> None:
    bind = op.get_bind()
    CAMPAIGN_KIND.create(bind, checkfirst=True)

    op.add_column(
        "campaigns",
        sa.Column("kind", CAMPAIGN_KIND, nullable=False, server_default="TEST"),
    )
    op.add_column("campaigns", sa.Column("code_prefix", sa.String(length=1), nullable=True))
    op.create_index("ix_campaigns_kind", "campaigns", ["kind"])

    op.add_column("promocodes", sa.Column("customer_card", sa.String(length=64), nullable=True))
    op.add_column("promocodes", sa.Column("customer_name", sa.String(length=128), nullable=True))
    op.add_column("promocodes", sa.Column("customer_phone", sa.String(length=32), nullable=True))
    op.create_unique_constraint(
        "uq_promocodes_campaign_customer",
        "promocodes",
        ["campaign_id", "customer_erp_id"],
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute("INSERT INTO app_settings (key, value) VALUES ('active_campaign_kind', 'TEST')")


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_constraint("uq_promocodes_campaign_customer", "promocodes", type_="unique")
    op.drop_column("promocodes", "customer_phone")
    op.drop_column("promocodes", "customer_name")
    op.drop_column("promocodes", "customer_card")
    op.drop_index("ix_campaigns_kind", table_name="campaigns")
    op.drop_column("campaigns", "code_prefix")
    op.drop_column("campaigns", "kind")
    CAMPAIGN_KIND.drop(op.get_bind(), checkfirst=True)
