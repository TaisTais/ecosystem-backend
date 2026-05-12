from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from src.core.security import hash_password
from src.models.users import User
from src.schemas.users import UserCreate, UserRead, UserUpdate


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Создание нового пользователя"""
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        role=user_data.role,
        # hashed_password=...  # добавим позже
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    """Получить пользователя по ID"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user


async def update_user(
    session: AsyncSession,
    current_user: User,
    data: UserUpdate
) -> User:
    """Обновление данных текущего пользователя"""

    # Проверка уникальности email
    if data.email is not None and data.email != current_user.email:
        result = await session.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует"
            )
        current_user.email = data.email

    # Обновление обычных полей
    if data.name is not None:
        current_user.name = data.name

    if data.description is not None:
        current_user.description = data.description

    # Обновление пароля (если передан)
    if data.password is not None:
        if len(data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль должен содержать минимум 6 символов"
            )
        current_user.hashed_password = hash_password(data.password)

    await session.commit()
    await session.refresh(current_user)

    return current_user
