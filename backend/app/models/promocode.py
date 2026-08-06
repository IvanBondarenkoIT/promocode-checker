import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PromocodeStatus


class Promocode(Base):
    __tablename__ = "promocodes"
    __table_args__ = (
        CheckConstraint("promocode ~ '^[0-9]{8}$'", name="ck_promocodes_promocode_8_digits"),
        Index("ix_promocodes_customer_erp_id", "customer_erp_id"),
        Index("ix_promocodes_promocode", "promocode"),
        Index("ix_promocodes_status", "status"),
        Index("ix_promocodes_expires_at", "expires_at"),
        Index("ix_promocodes_campaign_id", "campaign_id"),
        UniqueConstraint("campaign_id", "customer_erp_id", name="uq_promocodes_campaign_customer"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_erp_id: Mapped[str] = mapped_column(String(64), nullable=False)
    promocode: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    status: Mapped[PromocodeStatus] = mapped_column(
        Enum(PromocodeStatus, name="promocode_status"),
        nullable=False,
        default=PromocodeStatus.ACTIVE,
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_card: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign = relationship("Campaign", back_populates="promocodes")
    checker_logs = relationship("CheckerLog", back_populates="promocode")
