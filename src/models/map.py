from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from sqlalchemy import Enum as SQLEnum
from typing import Optional, List
from datetime import datetime, timezone

from src.database import Base


class SourceType(str, enum.Enum):
    LOCAL = "local"
    RECYCLEMAP = "recyclemap"


class EcoPointStatus(str, enum.Enum):
    WORKING = "working"
    CLOSED = "closed"
    TEMPORARILY_CLOSED = "temporarily_closed"


class EcoPointCategory(str, enum.Enum):
    PLASTIC = "plastic"
    GLASS = "glass"
    PAPER = "paper"
    METAL = "metal"
    BATTERIES = "batteries"
    ELECTRONICS = "electronics"
    CLOTHES = "clothes"
    HAZARDOUS = "hazardous"
    OTHER = "other"


class EcoPoint(Base):
    """Эко-точка на интерактивной карте"""
    __tablename__ = "ecopoint"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recyclemap_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    source: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), nullable=False, default=SourceType.LOCAL, index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[EcoPointCategory] = mapped_column(SQLEnum(EcoPointCategory), nullable=False, index=True)
    working_hours: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    needs_review: Mapped[bool] = mapped_column(default=False)
    recyclemap_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_local_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Связи
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_points"
    )
    statuses: Mapped[List["Status"]] = relationship(
        "Status",
        back_populates="point",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="point",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    visits: Mapped[List["Visit"]] = relationship(
        "Visit",
        back_populates="point",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Status(Base):
    """Класс для статусов пользователей к эко-точкам на интерактивной карте"""
    __tablename__ = "ecopoint_status"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[EcoPointStatus] = mapped_column(SQLEnum(EcoPointStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    point: Mapped["EcoPoint"] = relationship(
        "EcoPoint",
        back_populates="statuses"
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="statuses"
    )


class Review(Base):
    """Отзывы пользователей к эко-точкам на интерактивной карте"""
    __tablename__ = "ecopoint_review"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    point: Mapped["EcoPoint"] = relationship(
        "EcoPoint",
        back_populates="reviews"
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="reviews"
    )


class Visit(Base):
    """Посещение пользователем эко-точки"""
    __tablename__ = "ecopoint_visit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), nullable=False)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    proof_photo_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Связи
    visiters: Mapped["User"] = relationship(
        "User",
        back_populates="visits"
    )
    point: Mapped["EcoPoint"] = relationship(
        "EcoPoint",
        back_populates="visits"
    )

