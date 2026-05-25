from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.core.security import hash_password
from src.models.users import User
from src.schemas.users import UserUpdate
from src.services.moderation import get_moderations_by_user_id


async def get_my_moderations(
    session: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 20
):
    """Получить заявки текущего пользователя"""
    return await get_moderations_by_user_id(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


async def update_current_user(
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
