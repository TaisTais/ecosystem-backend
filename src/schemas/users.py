from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from src.models.users import UserRole


class UserBase(BaseModel):
    """Базовые поля пользователя"""
    name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
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
    """Схема для возврата данных пользователю"""
    id: int
    level: Optional[int] = 1
    experience_points: Optional[int] = 0
    is_blocked: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Обновление данных своего профиля"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    password: Optional[str] = None          # новое поле

    class Config:
        from_attributes = True


class ModeratorCreate(BaseModel):
    """Схема для создания модератора АДМИНОМ"""
    name: str
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def email_must_be_unique(cls, v):
        # Здесь можно добавить проверку, но обычно проверяем в сервисе
        return v
