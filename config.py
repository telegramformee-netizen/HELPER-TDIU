import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum as SAEnum,
    Float, ForeignKey, Integer, String, Text, JSON, SmallInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"
    id                 = Column(BigInteger, primary_key=True)
    username           = Column(String(64), nullable=True)
    full_name          = Column(String(128), nullable=True)
    hemis_id           = Column(String(64), nullable=True)
    hemis_password_enc = Column(Text, nullable=True)
    is_demo            = Column(Boolean, default=False)
    is_active          = Column(Boolean, default=True)
    tier               = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    notify_evening     = Column(Boolean, default=True)
    language_code      = Column(String(8), default="uz")
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), onupdate=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    user_id            = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    tier               = Column(SAEnum(SubscriptionTier), nullable=False)
    started_at         = Column(DateTime(timezone=True), nullable=False)
    expires_at         = Column(DateTime(timezone=True), nullable=False)
    telegram_charge_id = Column(String(128), nullable=True)
    amount_uzs         = Column(Integer, default=0)
    is_active          = Column(Boolean, default=True)


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("user_id", "subject_hemis_id"),)
    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    subject_name     = Column(String(256), nullable=False)
    subject_hemis_id = Column(String(64), nullable=True)
    current_score    = Column(Float, nullable=True)
    midterm_score    = Column(Float, nullable=True)
    final_score      = Column(Float, nullable=True)
    total_score      = Column(Float, nullable=True)
    total_hours      = Column(Integer, nullable=True)
    missed_hours     = Column(Integer, default=0)
    fail_risk        = Column(Boolean, default=False)
    needed_final     = Column(Float, nullable=True)
    semester         = Column(String(16), nullable=True)
    last_updated     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Schedule(Base):
    __tablename__ = "schedules"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    date         = Column(String(10), nullable=False)
    lesson_number= Column(SmallInteger, nullable=False)
    start_time   = Column(String(8), nullable=False)
    end_time     = Column(String(8), nullable=False)
    subject_name = Column(String(256), nullable=False)
    subject_type = Column(String(64), nullable=True)
    teacher_name = Column(String(128), nullable=True)
    room         = Column(String(64), nullable=True)
    building     = Column(String(64), nullable=True)
    content_hash = Column(String(64), nullable=True)
