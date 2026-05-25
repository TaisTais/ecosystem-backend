from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from src.core.security import hash_password
from src.models.users import User, UserRole
from src.schemas.admin import ModeratorCreate, AdminCreate


async def create_moderator(
    session: AsyncSession,
    admin: User,
    data: ModeratorCreate
) -> User:
    """Создание модератора администратором"""

    # Проверка, что текущий пользователь — администратор
    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Создавать модераторов может только администратор"
        )

    # Проверка уникальности email
    result = await session.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )

    moderator = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.MODERATOR,
        experience_points=0,
        created_at=datetime.now(timezone.utc)
    )

    session.add(moderator)
    await session.commit()
    await session.refresh(moderator)

    return moderator


async def create_admin(
    session: AsyncSession,
    data: AdminCreate
) -> User:
    """Создание главного администратора (используется в seed)"""
    result = await session.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Администратор с таким email уже существует"
        )

    admin = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.ADMIN,
        experience_points=0,
        created_at=datetime.now(timezone.utc)
    )

    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    return admin
