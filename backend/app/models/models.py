import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    contacts = relationship("TrustedContact", back_populates="user", cascade="all, delete-orphan")
    otp_records = relationship("OTPRecord", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("LocationRecord", back_populates="user", cascade="all, delete-orphan")
    safety_sessions = relationship("SafetySession", back_populates="user", cascade="all, delete-orphan")
    emergency_events = relationship("EmergencyEvent", back_populates="user", cascade="all, delete-orphan")


class TrustedContact(Base):
    __tablename__ = "trusted_contacts"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # normalized E.164, e.g. +91XXXXXXXXXX
    relationship_label = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    user = relationship("User", back_populates="contacts")


class OTPPurpose(str, enum.Enum):
    LOGIN = "login"


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    otp_hash = Column(String, nullable=False)
    purpose = Column(Enum(OTPPurpose), default=OTPPurpose.LOGIN)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="otp_records")


class LocationRecord(Base):
    __tablename__ = "location_records"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    session_id = Column(String, ForeignKey("safety_sessions.id"), nullable=True)
    timestamp = Column(DateTime, default=_now)

    user = relationship("User", back_populates="locations")


class SafetySessionStatus(str, enum.Enum):
    ACTIVE = "active"
    STOPPED = "stopped"


class SafetySession(Base):
    __tablename__ = "safety_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=_now)
    stopped_at = Column(DateTime, nullable=True)
    status = Column(Enum(SafetySessionStatus), default=SafetySessionStatus.ACTIVE)

    user = relationship("User", back_populates="safety_sessions")


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    status = Column(String, default="triggered")
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="emergency_events")
