import enum

from pydantic import BaseModel, field_validator, EmailStr, Field

from src.models.users import UserRole


class RegistrationRole(str, enum.Enum):
    CITIZEN = "citizen"
    ORGANIZATION = "organization"


class UserRegister(BaseModel):
    """Схема для создания пользователя (регистрация)"""
    name: str
    email: EmailStr
    password: str
    role: RegistrationRole = RegistrationRole.CITIZEN

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
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
