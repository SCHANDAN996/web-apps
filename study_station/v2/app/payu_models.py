"""Study Station's isolated one-time payment ledger; no card/contact data."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class PayUOrder(Base):
    __tablename__ = 'study_payu_order'
    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, index=True)
    account_namespace: Mapped[str] = mapped_column(String(64))
    plan_id: Mapped[str] = mapped_column(String(16))
    amount_paise: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default='INR')
    state: Mapped[str] = mapped_column(String(24), default='pending')
    binding: Mapped[str] = mapped_column(String(64))
    provider_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime)
    reconcile_error: Mapped[str | None] = mapped_column(String(40))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    revocation_reason: Mapped[str | None] = mapped_column(String(24))
    revocation_evidence: Mapped[str | None] = mapped_column(String(80))
