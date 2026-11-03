"""Google identities are keyed by immutable subject, never by an email address."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class GoogleIdentity(Base):
    __tablename__ = 'google_identity'
    subject: Mapped[str] = mapped_column(String(255), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('classroom_account.id'), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GoogleChallenge(Base):
    __tablename__ = 'google_challenge'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce: Mapped[str] = mapped_column(String(64))
    verifier: Mapped[str | None] = mapped_column(String(128))
    return_to: Mapped[str] = mapped_column(String(256), default='/classroom')
    expires: Mapped[datetime] = mapped_column(DateTime, index=True)
