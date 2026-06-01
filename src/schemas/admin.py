from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

from src.models import ModerationStatus
from src.models.achievements import ActionType


class ModeratorCreate(BaseModel):
    """Схема для создания модератора администратором"""
    name: str
    email: EmailStr
    password: str
    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v


class ModeratorActionRead(BaseModel):
    """Модератор + статистика его действий (для админа)"""
    id: int
    name: str
    email: EmailStr
    is_blocked: bool
    created_at: datetime
    actions_count: int = 0

    class Config:
        from_attributes = True


class ModeratorActionDetailRead(BaseModel):
    """Полная информация об одном действии модератора (для админа)"""
    id: int
    action_type: ActionType
    action_id: int
    user_id: int
    user_name: Optional[str] = None
    status: ModerationStatus
    created_at: datetime
    moderated_at: Optional[datetime] = None
    moderator_comment: Optional[str] = None
    old_data: Optional[dict] = None
    new_data: Optional[dict] = None

    class Config:
        from_attributes = True


class AdminCreate(BaseModel):
    """Схема для создания главного администратора (используется в seed)"""
    name: str
    email: EmailStr
    password: str
    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v
