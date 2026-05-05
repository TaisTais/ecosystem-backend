from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from src.models.users import User
from src.schemas.users import UserCreate, UserRead, UserUpdate


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Создание нового пользователя"""
    # Проверка на существование email
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


async def update_user(session: AsyncSession, user_id: int, user_data: UserUpdate) -> User:
    """Обновление данных пользователя"""
    user = await get_user_by_id(session, user_id)

    if user_data.name:
        user.name = user_data.name
    if user_data.email:
        user.email = user_data.email

    await session.commit()
    await session.refresh(user)
    return user
