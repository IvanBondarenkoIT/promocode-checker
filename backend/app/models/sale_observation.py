import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SaleObservation(Base):
    __tablename__ = "sale_observations"
    __table_args__ = (
        UniqueConstraint(
            "customer_erp_id",
            "order_id",
            name="uq_sale_observations_customer_order",
        ),
        Index("ix_sale_observations_promocode_id", "promocode_id"),
        Index("ix_sale_observations_customer_erp_id", "customer_erp_id"),
        Index("ix_sale_observations_verdict", "verdict"),
        Index("ix_sale_observations_detected_at", "detected_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promocode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("promocodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    promocode_value: Mapped[str | None] = mapped_column(String(20), nullable=True)
    customer_erp_id: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    qty_pieces: Mapped[float | None] = mapped_column(Float, nullable=True)
    products: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_ids: Mapped[str | None] = mapped_column(String(128), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    enforcement_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    promocode_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
