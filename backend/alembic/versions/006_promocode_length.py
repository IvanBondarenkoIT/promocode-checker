"""Widen promocode to 8-20 digits (loyalty card as code).

Revision ID: 006_promocode_length
Revises: 005_campaign_scope
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_promocode_length"
down_revision: str | Sequence[str] | None = "005_campaign_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_promocodes_promocode_8_digits", "promocodes", type_="check")
    op.alter_column(
        "promocodes",
        "promocode",
        existing_type=sa.String(length=8),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_promocodes_promocode_digits",
        "promocodes",
        "promocode ~ '^[0-9]{8,20}$'",
    )

    op.alter_column(
        "fraud_warnings",
        "promocode_value",
        existing_type=sa.String(length=8),
        type_=sa.String(length=20),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "fraud_warnings",
        "promocode_value",
        existing_type=sa.String(length=20),
        type_=sa.String(length=8),
        existing_nullable=True,
    )

    op.drop_constraint("ck_promocodes_promocode_digits", "promocodes", type_="check")
    op.alter_column(
        "promocodes",
        "promocode",
        existing_type=sa.String(length=20),
        type_=sa.String(length=8),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_promocodes_promocode_8_digits",
        "promocodes",
        "promocode ~ '^[0-9]{8}$'",
    )
