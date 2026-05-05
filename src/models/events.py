import enum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import Enum as SQLEnum
from src.database import Base
from src.models.complaints import Complaint
from src.models.users import User


class EventStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    FINISHED = "finished"


class Event(Base):
    """Класс для мероприятий в ленте постов и календаре"""
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    address: Mapped[Optional[str]] = mapped_column(String(300))
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500))
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[EventStatus] = mapped_column(SQLEnum(EventStatus), nullable=False, default=EventStatus.ACTIVE, index=True)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    organizers: Mapped[List["User"]] = relationship(
        "User",
        secondary="event_organizer",
        back_populates="organized_events",
        lazy="selectin"
    )
    applicants: Mapped[List["EventApplicant"]] = relationship(
        "EventApplicant",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    participants: Mapped[List["EventParticipant"]] = relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.target_id]",
        primaryjoin="and_(Complaint.target_id == Event.id, Complaint.target_type == 'event')",
        back_populates="events",
        lazy="selectin"
    )

    @property
    def applicants_count(self) -> int:
        return len(self.applicants)

    @property
    def participants_count(self) -> int:
        return len(self.participants)


class EventApplicant(Base):
    """Запись на мероприятия"""
    __tablename__ = "event_applicant"
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="applicants"
    )
    applicant: Mapped["User"] = relationship(
        "User",
    )


class EventParticipant(Base):
    """Посещение мероприятий"""
    __tablename__ = "event_participant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), nullable=False)
    participant_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    proof_photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="participants"
    )
    participant: Mapped["User"] = relationship(
        "User"
    )


# ==================== ПРОМЕЖУТОЧНЫЕ ТАБЛИЦЫ ====================

class EventOrganizer(Base):
    """Промежуточная таблица: User(организаторы) - Event(мероприятия)"""
    __tablename__ = "event_organizer"
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
