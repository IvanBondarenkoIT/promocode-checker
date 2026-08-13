from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

RECONCILE_STATE_ID = 1


class ReconcileState(Base):
    """Single-row cursor for ERP observe window (overlap + no growing tail)."""

    __tablename__ = "reconcile_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_scan_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_erp_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_erp_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
