from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from typing import Optional
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
from src.database import Base


class ActionType(str, enum.Enum):
    ADD_POINT = "add_point"
    SET_STATUS = "set_status"
    WRITE_REVIEW = "write_review"
    PARTICIPATE_EVENT = "participate_event"
    ORGANIZE_EVENT = "organize_event"
    VISIT_RECYCLING_POINT = "visit_recycling_point"
    VISIT_OWN_TARA_POINT = "visit_own_tara_point"


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class Achievement(Base):
    """Класс шаблон достижения"""
    __tablename__ = "achievement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(200))
    points_reward: Mapped[int] = mapped_column(Integer, default=0)

    # Награда
    badge_icon: Mapped[Optional[str]] = mapped_column(String(200))  # название файла иконки награды
    is_cumulative: Mapped[bool] = mapped_column(default=False)  # накопительное ли

    # Условия получения
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType), nullable=False)
    required_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    """Достижения пользователей"""
    __tablename__ = "user_achievement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievement.id"), nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="achievements"
    )
    achievement: Mapped["Achievement"] = relationship(
        "Achievement"
    )


class ModerationRecord(Base):
    """Универсальная таблица модерации всех пользовательских действий"""
    __tablename__ = "moderation_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType), nullable=False)
    action_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    moderator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    status: Mapped[ModerationStatus] = mapped_column(SQLEnum(ModerationStatus), nullable=False, default=ModerationStatus.PENDING, index=True)

    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderator_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    achievement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_achievement.id"), nullable=True)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Связи
    users: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    moderator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[moderator_id]
    )
