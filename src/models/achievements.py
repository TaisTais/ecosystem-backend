from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import Enum as SQLEnum
from src.database import Base


class ActionType(str, enum.Enum):
    ADD_POINT = "add_point"
    UPDATE_POINT = "update_point"
    SET_STATUS = "set_status"
    WRITE_REVIEW = "write_review"
    PARTICIPATE_EVENT = "participate_event"
    ORGANIZE_EVENT = "organize_event"
    VISIT_RECYCLING_POINT = "visit_recycling_point"
    VISIT_OWN_TARA_POINT = "visit_own_tara_point"


class Achievement(Base):
    """Класс шаблон достижения"""
    __tablename__ = "achievement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(200))
    points_reward: Mapped[int] = mapped_column(Integer, default=0)

    # Награда
    badge_icon: Mapped[Optional[str]] = mapped_column(String(200))
    is_cumulative: Mapped[bool] = mapped_column(default=False)

    # Условия получения
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType), nullable=False)
    required_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
