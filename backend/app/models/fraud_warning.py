import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import FraudWarningStatus


class FraudWarning(Base):
    __tablename__ = "fraud_warnings"
    __table_args__ = (
        Index("ix_fraud_warnings_promocode_id", "promocode_id"),
        Index("ix_fraud_warnings_status", "status"),
        Index("ix_fraud_warnings_detected_at", "detected_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promocode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("promocodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    checker_log_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("checker_logs.id", ondelete="SET NULL"),
        nullable=True,
    )
    point_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_erp_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    promocode_value: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[FraudWarningStatus] = mapped_column(
        Enum(FraudWarningStatus, name="fraud_warning_status"),
        nullable=False,
        default=FraudWarningStatus.OPEN,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
