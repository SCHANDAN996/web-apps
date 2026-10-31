"""Encrypted SDK choice and Google external-report outbox, isolated from website orders."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class PlayChoice(Base):
    __tablename__ = 'study_play_choice'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    namespace: Mapped[str] = mapped_column(String(64), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    token_encrypted: Mapped[str] = mapped_column(Text)
    plan_id: Mapped[str] = mapped_column(String(16))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    order_id: Mapped[str | None] = mapped_column(String(48), unique=True)
    administrative_area: Mapped[str | None] = mapped_column(String(64))
    pretax_paise: Mapped[int | None] = mapped_column(Integer)
    tax_paise: Mapped[int | None] = mapped_column(Integer)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime)
    provider_id: Mapped[str | None] = mapped_column(String(64))
    amount_paise: Mapped[int | None] = mapped_column(Integer)
    provider_binding: Mapped[str | None] = mapped_column(String(64))
    provider_account_hash: Mapped[str | None] = mapped_column(String(64))
    account_deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    purge_after: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    refunded_paise: Mapped[int] = mapped_column(Integer, default=0)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    last_error: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
