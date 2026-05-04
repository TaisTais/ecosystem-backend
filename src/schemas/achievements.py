from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.models.achievements import ActionType, ModerationStatus


class AchievementBase(BaseModel):
    """Базовая информация о достижении"""
    name: str
    description: str
    icon: Optional[str] = None
    points_reward: int = 0
    badge_icon: Optional[str] = None
    is_cumulative: bool = False
    action_type: ActionType
    required_count: Optional[int] = None


class AchievementCreate(AchievementBase):
    """Создание нового шаблона достижения (админом)"""
    is_active: bool = True


class AchievementRead(AchievementBase):
    """Полная информация о шаблоне достижения"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementUpdate(BaseModel):
    """Редактирование шаблона достижения"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    points_reward: Optional[int] = None
    badge_icon: Optional[str] = None
    is_cumulative: Optional[bool] = None
    required_count: Optional[int] = None
    is_active: Optional[bool] = None


class UserAchievementRead(BaseModel):
    """Достижение пользователя (для профиля)"""
    id: int
    achievement_id: int
    name: str
    description: str
    icon: Optional[str] = None
    badge_icon: Optional[str] = None
    points_reward: int
    achieved_at: datetime
    is_cumulative: bool

    class Config:
        from_attributes = True


class UserAchievementList(BaseModel):
    """Список достижений пользователя"""
    achievements: List[UserAchievementRead]


class ModerationRecordRead(BaseModel):
    """Информация о модерации (для модератора и пользователя)"""
    id: int
    action_id: int
    action_type: ActionType
    user_id: int
    user_name: Optional[str] = None
    status: ModerationStatus
    rejection_reason: Optional[str] = None
    moderator_comment: Optional[str] = None
    submitted_at: datetime
    moderated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModerationDecision(BaseModel):
    """Решение модератора"""
    status: ModerationStatus
    rejection_reason: Optional[str] = None
    moderator_comment: Optional[str] = None
