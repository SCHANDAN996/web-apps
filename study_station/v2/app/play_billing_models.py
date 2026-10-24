"""Encrypted Google purchase-token ledger, separate from website entitlements."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class PlayPurchase(Base):
    __tablename__ = 'study_play_purchase'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_encrypted: Mapped[str] = mapped_column(Text)
    namespace: Mapped[str] = mapped_column(String(64), index=True)
    product_id: Mapped[str] = mapped_column(String(100))
    base_plan_id: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    entitled: Mapped[bool] = mapped_column(Boolean, default=False)
    test_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
