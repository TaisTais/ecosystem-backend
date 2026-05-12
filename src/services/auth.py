from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timezone
from src.models.users import User
from src.schemas.users import UserCreate, UserLogin, Token
from src.core.security import hash_password, verify_password, create_access_token


async def register_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Регистрация нового пользователя"""

    print(f"DEBUG: Registering user with email={user_data.email}, password length={len(user_data.password)}")

    # Проверка существования
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")

    # Хэширование
    hashed_password = hash_password(user_data.password)
    print(f"DEBUG: Password hashed successfully, length of hash = {len(hashed_password)}")

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        experience_points=0,
        created_at=datetime.now(timezone.utc)
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


async def authenticate_user(session: AsyncSession, login_data: UserLogin) -> Token:
    """Авторизация пользователя и выдача токена"""

    result = await session.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаём JWT-токен
    token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    )

    return Token(access_token=token)
