"""Server-owned membership periods; never populated from a checkout client response."""
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Membership(Base):
    __tablename__ = 'membership'
    # Permanent opaque account namespace, not a recyclable integer ID.
    namespace: Mapped[str] = mapped_column(String(64), primary_key=True)
    trial_started_at: Mapped[datetime] = mapped_column(DateTime)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime)
    paid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trial_policy_version: Mapped[str | None] = mapped_column(String(40), nullable=True)

class MembershipGrant(Base):
    __tablename__ = 'membership_grant'
    # Verified provider transaction reference, not client-supplied request ID.
    reference: Mapped[str] = mapped_column(String(160), primary_key=True)
    namespace: Mapped[str] = mapped_column(String(64), index=True)
    plan_id: Mapped[str] = mapped_column(String(24))
    verified_at: Mapped[datetime] = mapped_column(DateTime)
    paid_until: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TrialRollout(Base):
    """Global non-personal marker: the first apply fixes the rollout date forever."""
    __tablename__ = 'membership_trial_rollout'
    version: Mapped[str] = mapped_column(String(40), primary_key=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime)
