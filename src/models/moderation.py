from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import Enum as SQLEnum
from src.database import Base
from src.models.achievements import ActionType


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationRecord(Base):
    """Универсальная таблица модерации всех пользовательских действий"""
    __tablename__ = "moderation_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType), nullable=False)
    action_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    old_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    moderator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    status: Mapped[ModerationStatus] = mapped_column(SQLEnum(ModerationStatus), nullable=False, default=ModerationStatus.PENDING, index=True)
    moderator_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    achievement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_achievement.id"), nullable=True)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    moderator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[moderator_id]
    )
