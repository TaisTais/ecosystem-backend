from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from src.models.users import UserRole


class UserBase(BaseModel):
    """Базовые поля пользователя"""
    id: int
    name: str
    email: EmailStr
    role: UserRole


class UserRegister(UserBase):
    """Схема для создания пользователя (регистрация)"""
    password: str
    role: UserRole = UserRole.CITIZEN

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: UserRole) -> UserRole:
        if v not in {UserRole.CITIZEN, UserRole.ORGANIZATION}:
            raise ValueError('При регистрации доступны только citizen и organization')
        return v


class UserLogin(BaseModel):
    """Авторизация (логин)"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Ответ сервера после успешного логина"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные, которые хранятся внутри JWT-токена"""
    user_id: int
    email: str
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
    description: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True
