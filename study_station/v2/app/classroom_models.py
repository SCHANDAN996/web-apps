"""Additive account/classroom storage. Private guest progress is deliberately separate."""
from datetime import datetime
from sqlalchemy import String, Text, Integer, JSON, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class ClassroomAccount(Base):
    __tablename__ = 'classroom_account'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    password: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ClassroomSession(Base):
    __tablename__ = 'classroom_session'
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('classroom_account.id'), index=True)
    expires: Mapped[datetime] = mapped_column(DateTime)

class ClassroomRecord(Base):
    __tablename__ = 'classroom_record'
    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('classroom_account.id'), index=True)
    parent: Mapped[str | None] = mapped_column(String(48), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    share_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ClassroomMember(Base):
    __tablename__ = 'classroom_member'
    __table_args__ = (UniqueConstraint('group_id', 'account_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[str] = mapped_column(ForeignKey('classroom_record.id'), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('classroom_account.id'), index=True)
    role: Mapped[str] = mapped_column(String(16), default='student')

class ClassroomEvent(Base):
    __tablename__ = 'classroom_event'
    __table_args__ = (UniqueConstraint('room_id', 'op_id'), UniqueConstraint('room_id', 'seq'))
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey('classroom_record.id'), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('classroom_account.id'))
    op_id: Mapped[str] = mapped_column(String(80))
    seq: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)

class ClassroomOperation(Base):
    __tablename__ = 'classroom_operation'
    __table_args__ = (UniqueConstraint('account_id', 'op_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('classroom_account.id'))
    op_id: Mapped[str] = mapped_column(String(80))
    fingerprint: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)

class ClassroomRate(Base):
    __tablename__ = 'classroom_rate'
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    expires: Mapped[datetime] = mapped_column(DateTime)
