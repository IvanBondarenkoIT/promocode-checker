import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CheckerActionType


class CheckerLog(Base):
    __tablename__ = "checker_logs"
    __table_args__ = (
        Index("ix_checker_logs_promocode_id", "promocode_id"),
        Index("ix_checker_logs_scan_time", "scan_time"),
        Index("ix_checker_logs_point_id", "point_id"),
        Index("ix_checker_logs_action_type", "action_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promocode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("promocodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    scanned_code: Mapped[str] = mapped_column(String(32), nullable=False)
    scan_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    action_type: Mapped[CheckerActionType] = mapped_column(
        Enum(CheckerActionType, name="checker_action_type"),
        nullable=False,
    )
    point_id: Mapped[str] = mapped_column(String(64), nullable=False)
    erp_sale_matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    promocode = relationship("Promocode", back_populates="checker_logs")
