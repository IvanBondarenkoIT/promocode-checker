from datetime import UTC, date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.services.telegram_topics import (
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    DEFAULT_TOPICS_CSV,
)

# Re-export modes for callers that import from the model module.
__all__ = [
    "ALERT_MODE_DIGEST",
    "ALERT_MODE_FULL",
    "TelegramBotState",
    "TelegramDigestState",
    "TelegramSubscriber",
]


class TelegramSubscriber(Base):
    __tablename__ = "telegram_subscribers"

    chat_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    alert_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ALERT_MODE_FULL, server_default=ALERT_MODE_FULL
    )
    topics: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=DEFAULT_TOPICS_CSV,
        server_default=DEFAULT_TOPICS_CSV,
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )


class TelegramBotState(Base):
    __tablename__ = "telegram_bot_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    update_offset: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TelegramDigestState(Base):
    __tablename__ = "telegram_digest_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_day_start_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_eod_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
