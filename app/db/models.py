from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timedelta, timezone


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    bookings = relationship("Booking", back_populates="user")


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    time_slots = relationship("TimeSlot", back_populates="service")


class Trainer(Base):
    __tablename__ = "trainers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    bio = Column(Text, nullable=False)
    time_slots = relationship("TimeSlot", back_populates="trainer")


class TimeSlot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    booked_count = Column(Integer, default=0, nullable=False)
    capacity = Column(Integer, nullable=False)
    bookings = relationship("Booking", back_populates="slot")
    service = relationship("Service", back_populates="time_slots")
    trainer = relationship("Trainer", back_populates="time_slots")


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    status = Column(
        Enum("confirmed", "cancelled", name="booking_status"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="bookings")
    slot = relationship("TimeSlot", back_populates="bookings")
