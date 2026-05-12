from sqlalchemy import String, Integer, DateTime, Text, and_, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign, remote
import enum
from sqlalchemy import Enum as SQLEnum
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

from src.database import Base
from src.models.achievements import UserAchievement
from src.models.events import Event, EventApplicant, EventParticipant
from src.models.feed import Post
from src.models.map import Status, Review, EcoPoint, Visit

if TYPE_CHECKING:
    from src.models.complaints import Complaint


class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    ORGANIZATION = "organization"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    """Универсальный класс для всех видов пользователей"""
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.CITIZEN, index=True)

    # Общие поля
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    block_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Поля для обычных пользователей
    experience_points: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Поля для организаций
    description: Mapped[Optional[str]] = mapped_column(Text)
    inn: Mapped[Optional[str]] = mapped_column(String(20))

    # Связи
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author",
        lazy="selectin"
    )
    statuses: Mapped[List["Status"]] = relationship(
        "Status",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    created_points: Mapped[List["EcoPoint"]] = relationship(
        "EcoPoint",
        back_populates="created_by",
        lazy="selectin"
    )
    organized_events: Mapped[List["Event"]] = relationship(
        "Event",
        secondary="event_organizer",
        back_populates="organizers",
        lazy="selectin"
    )
    applied_events: Mapped[List["EventApplicant"]] = relationship(
        "EventApplicant",
        back_populates="applicant",
        lazy="selectin"
    )
    participated_events: Mapped[List["EventParticipant"]] = relationship(
        "EventParticipant",
        back_populates="participant",
        lazy="selectin"
    )
    visits: Mapped[List["Visit"]] = relationship(
        "Visit",
        back_populates="visiters",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement",
        back_populates="user",
        lazy="selectin"
    )
    complaints_made: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.complainant_id]",
        back_populates="complainant",
        lazy="selectin"
    )
    complaints_received: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        primaryjoin="and_(User.id == foreign(Complaint.target_id), Complaint.target_type == 'user')",
        back_populates="users",
        lazy="selectin",
        viewonly=True,
    )
