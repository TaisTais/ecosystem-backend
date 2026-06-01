from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from src.core.security import hash_password
from src.models import ModerationRecord
from src.models.users import User, UserRole
from src.schemas.admin import ModeratorCreate, AdminCreate, ModeratorActionRead, ModeratorActionDetailRead


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


async def get_all_moderators(
    session: AsyncSession,
    admin: User,
    skip: int = 0,
    limit: int = 50
) -> List[ModeratorActionRead]:
    """Получить всех модераторов + статистику их модераций (для админа)"""

    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Эти данные может получить только администратор"
        )

    # Получаем модераторов
    result = await session.execute(
        select(User)
        .where(User.role == UserRole.MODERATOR)
        .offset(skip)
        .limit(limit)
    )
    moderators = result.scalars().all()

    response = []
    for mod in moderators:
        actions_count_query = await session.execute(
            select(func.count(ModerationRecord.id))
            .where(ModerationRecord.moderator_id == mod.id)
        )
        actions_count = actions_count_query.scalar() or 0

        response.append(ModeratorActionRead(
            id=mod.id,
            name=mod.name,
            email=mod.email,
            is_blocked=mod.is_blocked,
            created_at=mod.created_at,
            actions_count=actions_count
        ))

    return response


async def get_moderator_detail(
    session: AsyncSession,
    admin: User,
    moderator_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ModeratorActionDetailRead]:
    """Админ получает полную историю действий конкретного модератора"""
    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Эти данные может получить только администратор"
        )

    mod_result = await session.execute(
        select(User).where(User.id == moderator_id, User.role == UserRole.MODERATOR)
    )
    moderator = mod_result.scalar_one_or_none()
    if not moderator:
        raise HTTPException(
            status_code=404,
            detail="Модератор с таким id не найден"
        )

    result = await session.execute(
        select(ModerationRecord)
        .where(ModerationRecord.moderator_id == moderator_id)
        .order_by(ModerationRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(ModerationRecord.user),      # для user_name
            selectinload(ModerationRecord.moderator)  # на всякий случай
        )
    )

    actions = result.scalars().all()

    return [
        ModeratorActionDetailRead(
            id=action.id,
            action_type=action.action_type,
            action_id=action.action_id,
            user_id=action.user_id,
            user_name=action.user.name if action.user else None,
            status=action.status,
            created_at=action.created_at,
            moderated_at=action.moderated_at,
            moderator_comment=action.moderator_comment,
            old_data=action.old_data,
            new_data=action.new_data,
        )
        for action in actions
    ]


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
