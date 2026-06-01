from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from src.models.users import User, UserRole


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


async def get_users_list(
    session: AsyncSession,
    role: Optional[UserRole] = None,
    skip: int = 0,
    limit: int = 50,
    is_public: bool = False   # новый флаг
) -> List[User]:
    """
    Получить список пользователей.
    - is_public=True → для обычных пользователей (только активные)
    - is_public=False → для модераторов (все пользователи)
    """
    query = select(User).order_by(
        User.experience_points.desc(),
        User.created_at.desc()
    )
    if role is not None:
        query = query.where(User.role == role)
    if is_public:
        query = query.where(User.is_blocked == False)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def block_user(session: AsyncSession, user_id: int, moderator: User, reason: Optional[str] = None) -> User:
    """Заблокировать пользователя"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Защита: модератор не может заблокировать другого модератора или админа
    if user.role in [UserRole.MODERATOR, UserRole.ADMIN] and moderator.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Модератор не может блокировать других модераторов или администраторов"
        )

    user.is_blocked = True
    user.blocked_at = datetime.now(timezone.utc)
    user.block_reason = reason or "Заблокирован модератором"

    await session.commit()
    await session.refresh(user)

    return user


async def unblock_user(
    session: AsyncSession,
    user_id: int,
    moderator: User
) -> User:
    """Разблокировать пользователя"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.role in [UserRole.MODERATOR, UserRole.ADMIN] and moderator.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Модератор не может разблокировать других модераторов или администраторов"
        )

    user.is_blocked = False
    user.blocked_at = None
    user.block_reason = None

    await session.commit()
    await session.refresh(user)
    return user
