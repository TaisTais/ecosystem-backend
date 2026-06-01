from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from src.models.users import UserRole


class UserBase(BaseModel):
    """Базовые поля пользователя"""
    id: int
    name: str
    email: EmailStr
    role: UserRole


class UserRead(UserBase):
    """Полная информация о пользователе (для профиля)"""
    is_blocked: bool
    blocked_at: Optional[datetime] = None
    block_reason: Optional[str] = None
    created_at: datetime
    experience_points: int
    level: Optional[int] = None
    description: Optional[str] = None
    inn: Optional[str] = None   # только для организаций

    class Config:
        from_attributes = True


class UserPublicRead(BaseModel):
    """Публичная информация о пользователе (для всех авторизованных пользователей)"""
    id: int
    name: str
    role: UserRole
    level: Optional[int] = None
    experience_points: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserPublicListRead(BaseModel):
    """Публичная информация пользователя для списков (для всех)"""
    id: int
    name: str
    role: UserRole
    level: Optional[int] = None
    experience_points: Optional[int] = None

    class Config:
        from_attributes = True


class UserListRead(UserBase):
    """Расширенная информация для модераторов и администраторов"""
    is_blocked: bool
    level: Optional[int] = None
    experience_points: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Обновление данных своего профиля"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    description: Optional[str] = None
    inn: Optional[str] = None

    class Config:
        from_attributes = True
