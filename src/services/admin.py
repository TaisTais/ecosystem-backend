from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from src.core.security import hash_password
from src.models import ModerationRecord
from src.models.users import User, UserRole
from src.schemas.admin import ModeratorCreate, AdminCreate


async def create_admin(session: AsyncSession, data: AdminCreate) -> User:
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
        is_blocked=False,
        created_at=datetime.now(timezone.utc)
    )

    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def create_moderator(session: AsyncSession, admin: User, data: ModeratorCreate) -> User:
    """Создание модератора администратором"""

    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Создавать модераторов может только администратор"
        )

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


async def get_all_moderators_with_stats(
    session: AsyncSession,
    admin: User,
    skip: int = 0,
    limit: int = 50
) -> List[dict]:
    """Получить всех модераторов + статистику их модераций (для админа)"""

    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Эти данные может получить только администратор"
        )
    result = await session.execute(
        select(User)
        .where(User.role == UserRole.MODERATOR)
        .offset(skip)
        .limit(limit)
    )
    moderators = result.scalars().all()

    response = []
    for mod in moderators:
        mod_actions = await session.execute(
            select(func.count(ModerationRecord.id))
            .where(ModerationRecord.moderator_id == mod.id)
        )
        actions_count = mod_actions.scalar() or 0

        response.append({
            "id": mod.id,
            "name": mod.name,
            "email": mod.email,
            "is_blocked": mod.is_blocked,
            "created_at": mod.created_at,
            "actions_count": actions_count
        })

    return response


async def block_moderator(
        session: AsyncSession,
        moderator_id: int,
        admin: User,
        reason: Optional[str] = None
) -> dict:
    """Удаление (блокировка) модератора администратором"""

    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Управлять модераторами может только администратор"
        )

    if moderator_id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Администратор не может удалить сам себя"
        )

    result = await session.execute(
        select(User).where(User.id == moderator_id)
    )
    moderator = result.scalar_one_or_none()

    if not moderator:
        raise HTTPException(status_code=404, detail="Модератор не найден")

    if moderator.role != UserRole.MODERATOR:
        raise HTTPException(
            status_code=400,
            detail="Удалять можно только пользователей с ролью MODERATOR"
        )

    moderator.is_blocked = True
    moderator.blocked_at = datetime.now(timezone.utc)
    moderator.block_reason = reason or "Удалён администратором"

    await session.commit()

    return {
        "success": True,
        "message": "Модератор заблокирован",
        "moderator_id": moderator_id,
    }


async def unblock_moderator(
    session: AsyncSession,
    moderator_id: int,
    admin: User
) -> dict:
    """Разблокировка модератора"""

    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Управлять модераторами может только администратор"
        )

    if moderator_id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя разблокировать самого себя")

    result = await session.execute(
        select(User).where(User.id == moderator_id)
    )
    moderator = result.scalar_one_or_none()

    if not moderator:
        raise HTTPException(status_code=404, detail="Модератор не найден")

    if moderator.role != UserRole.MODERATOR:
        raise HTTPException(status_code=400, detail="Разблокировать можно только модераторов")

    if not moderator.is_blocked:
        raise HTTPException(status_code=400, detail="Модератор не заблокирован")

    moderator.is_blocked = False
    moderator.blocked_at = None
    moderator.block_reason = None

    await session.commit()
    await session.refresh(moderator)

    return {
        "success": True,
        "message": "Модератор разблокирован",
        "moderator_id": moderator_id
    }
