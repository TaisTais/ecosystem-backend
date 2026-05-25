from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


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
