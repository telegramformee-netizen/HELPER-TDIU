"""
database.py — SQLite (aiosqlite) + SQLAlchemy ORM
Railway'da PostgreSQL yo'q — SQLite bilan boshlaymiz.
Keyinchalik DATABASE_URL ni o'zgartirsangiz PostgreSQL ga o'tadi.
"""
import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum as SAEnum,
    Float, Integer, String, Text, SmallInteger, UniqueConstraint
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class SubscriptionTier(str, enum.Enum):
    FREE    = "free"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"
    id                 = Column(BigInteger, primary_key=True)   # Telegram ID
    username           = Column(String(64), nullable=True)
    full_name          = Column(String(128), nullable=True)
    hemis_id           = Column(String(64), nullable=True)
    hemis_password_enc = Column(Text, nullable=True)            # AES shifrlangan
    is_demo            = Column(Boolean, default=False)
    is_active          = Column(Boolean, default=True)
    tier               = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    notify_evening     = Column(Boolean, default=True)
    language_code      = Column(String(8), default="uz")
    created_at         = Column(DateTime, server_default=func.now())


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("user_id", "subject_name"),)
    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(BigInteger, nullable=False)
    subject_name    = Column(String(256), nullable=False)
    subject_hemis_id= Column(String(64), nullable=True)
    current_score   = Column(Float, nullable=True)   # max 20
    midterm_score   = Column(Float, nullable=True)   # max 30
    final_score     = Column(Float, nullable=True)   # max 50
    total_score     = Column(Float, nullable=True)
    total_hours     = Column(Integer, nullable=True)
    missed_hours    = Column(Integer, nullable=True, default=0)
    fail_risk       = Column(Boolean, default=False)
    needed_final    = Column(Float, nullable=True)
    semester        = Column(String(16), nullable=True)
    last_updated    = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Schedule(Base):
    __tablename__ = "schedules"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(BigInteger, nullable=False)
    date         = Column(String(10), nullable=False)   # "2024-09-02"
    lesson_num   = Column(SmallInteger, nullable=False)
    start_time   = Column(String(8), nullable=False)
    end_time     = Column(String(8), nullable=False)
    subject      = Column(String(256), nullable=False)
    subject_type = Column(String(64), nullable=True)
    teacher      = Column(String(128), nullable=True)
    room         = Column(String(64), nullable=True)
    building     = Column(String(64), nullable=True)


class Room(Base):
    __tablename__ = "rooms"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    code      = Column(String(32), unique=True)
    building  = Column(String(64))
    floor     = Column(SmallInteger, nullable=True)
    capacity  = Column(SmallInteger, nullable=True)
    room_type = Column(String(64), nullable=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Namunali xonalar qo'shish
    async with AsyncSessionFactory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Room).limit(1))
        if not res.scalars().first():
            rooms = [
                Room(code="A-101", building="A blok", floor=1, capacity=120, room_type="Ma'ruza zali"),
                Room(code="A-201", building="A blok", floor=2, capacity=80,  room_type="Ma'ruza zali"),
                Room(code="A-301", building="A blok", floor=3, capacity=100, room_type="Ma'ruza zali"),
                Room(code="B-101", building="B blok", floor=1, capacity=50,  room_type="Seminar xona"),
                Room(code="B-204", building="B blok", floor=2, capacity=30,  room_type="Seminar xona"),
                Room(code="C-101", building="C blok", floor=1, capacity=40,  room_type="Kompyuter lab"),
                Room(code="AKTOV", building="Asosiy", floor=1, capacity=500, room_type="Aktov zal"),
            ]
            for r in rooms:
                session.add(r)
            await session.commit()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
