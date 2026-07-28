"""Initial schema for promocode checker.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

promocode_status = postgresql.ENUM("ACTIVE", "USED", name="promocode_status", create_type=False)
checker_action_type = postgresql.ENUM(
    "SCAN_CHECK",
    "MANUAL_CLOSE",
    "AUTO_CLOSE",
    name="checker_action_type",
    create_type=False,
)
fraud_warning_status = postgresql.ENUM(
    "OPEN",
    "REVIEWED",
    "DISMISSED",
    name="fraud_warning_status",
    create_type=False,
)
admin_role = postgresql.ENUM("admin", "viewer", name="admin_role", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    promocode_status.create(bind, checkfirst=True)
    checker_action_type.create(bind, checkfirst=True)
    fraud_warning_status.create(bind, checkfirst=True)
    admin_role.create(bind, checkfirst=True)

    op.create_table(
        "promocodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_erp_id", sa.String(length=64), nullable=False),
        sa.Column("promocode", sa.String(length=8), nullable=False),
        sa.Column("status", promocode_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("promocode ~ '^[0-9]{8}$'", name="ck_promocodes_promocode_8_digits"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("promocode"),
    )
    op.create_index("ix_promocodes_customer_erp_id", "promocodes", ["customer_erp_id"])
    op.create_index("ix_promocodes_promocode", "promocodes", ["promocode"])
    op.create_index("ix_promocodes_status", "promocodes", ["status"])
    op.create_index("ix_promocodes_expires_at", "promocodes", ["expires_at"])

    op.create_table(
        "checker_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("promocode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scanned_code", sa.String(length=32), nullable=False),
        sa.Column(
            "scan_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("action_type", checker_action_type, nullable=False),
        sa.Column("point_id", sa.String(length=64), nullable=False),
        sa.Column(
            "erp_sale_matched",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.ForeignKeyConstraint(["promocode_id"], ["promocodes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checker_logs_promocode_id", "checker_logs", ["promocode_id"])
    op.create_index("ix_checker_logs_scan_time", "checker_logs", ["scan_time"])
    op.create_index("ix_checker_logs_point_id", "checker_logs", ["point_id"])
    op.create_index("ix_checker_logs_action_type", "checker_logs", ["action_type"])

    op.create_table(
        "fraud_warnings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("promocode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checker_log_id", sa.BigInteger(), nullable=True),
        sa.Column("point_id", sa.String(length=64), nullable=True),
        sa.Column("customer_erp_id", sa.String(length=64), nullable=True),
        sa.Column("promocode_value", sa.String(length=8), nullable=True),
        sa.Column("status", fraud_warning_status, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["checker_log_id"], ["checker_logs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["promocode_id"], ["promocodes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fraud_warnings_promocode_id", "fraud_warnings", ["promocode_id"])
    op.create_index("ix_fraud_warnings_status", "fraud_warnings", ["status"])
    op.create_index("ix_fraud_warnings_detected_at", "fraud_warnings", ["detected_at"])

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor_username", sa.String(length=64), nullable=False),
        sa.Column("actor_role", admin_role, nullable=False),
        sa.Column("entity_name", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("promocode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"])
    op.create_index(
        "ix_admin_audit_logs_entity",
        "admin_audit_logs",
        ["entity_name", "entity_id"],
    )
    op.create_index("ix_admin_audit_logs_actor", "admin_audit_logs", ["actor_username"])

    op.create_table(
        "telegram_notification_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("chat_id", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="sent"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_telegram_notification_logs_created_at",
        "telegram_notification_logs",
        ["created_at"],
    )
    op.create_index(
        "ix_telegram_notification_logs_dedup_key",
        "telegram_notification_logs",
        ["dedup_key"],
    )
    op.create_index(
        "ix_telegram_notification_logs_event_type",
        "telegram_notification_logs",
        ["event_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_telegram_notification_logs_event_type",
        table_name="telegram_notification_logs",
    )
    op.drop_index(
        "ix_telegram_notification_logs_dedup_key",
        table_name="telegram_notification_logs",
    )
    op.drop_index(
        "ix_telegram_notification_logs_created_at",
        table_name="telegram_notification_logs",
    )
    op.drop_table("telegram_notification_logs")

    op.drop_index("ix_admin_audit_logs_actor", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_entity", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")

    op.drop_index("ix_fraud_warnings_detected_at", table_name="fraud_warnings")
    op.drop_index("ix_fraud_warnings_status", table_name="fraud_warnings")
    op.drop_index("ix_fraud_warnings_promocode_id", table_name="fraud_warnings")
    op.drop_table("fraud_warnings")

    op.drop_index("ix_checker_logs_action_type", table_name="checker_logs")
    op.drop_index("ix_checker_logs_point_id", table_name="checker_logs")
    op.drop_index("ix_checker_logs_scan_time", table_name="checker_logs")
    op.drop_index("ix_checker_logs_promocode_id", table_name="checker_logs")
    op.drop_table("checker_logs")

    op.drop_index("ix_promocodes_expires_at", table_name="promocodes")
    op.drop_index("ix_promocodes_status", table_name="promocodes")
    op.drop_index("ix_promocodes_promocode", table_name="promocodes")
    op.drop_index("ix_promocodes_customer_erp_id", table_name="promocodes")
    op.drop_table("promocodes")

    bind = op.get_bind()
    admin_role.drop(bind, checkfirst=True)
    fraud_warning_status.drop(bind, checkfirst=True)
    checker_action_type.drop(bind, checkfirst=True)
    promocode_status.drop(bind, checkfirst=True)
