from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from src.core.security import hash_password
from src.models import ModerationRecord, User, Complaint
from src.models.users import User, UserRole
from src.schemas.complaints import ComplaintList, ComplaintRead
from src.schemas.moderation import ModerationRecordDetailRead
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


async def get_my_moderation_actions(
    session: AsyncSession,
    current_moderator: User,
    skip: int = 0,
    limit: int = 50
) -> List[ModerationRecordDetailRead]:
    """Посмотреть свои действия по модерации"""
    result = await session.execute(
        select(ModerationRecord)
        .where(ModerationRecord.moderator_id == current_moderator.id)
        .order_by(ModerationRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(ModerationRecord.user))   # для user_name
    )
    actions = result.scalars().all()
    return [ModerationRecordDetailRead.model_validate(action) for action in actions]


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

    if current_user.role == UserRole.ORGANIZATION:
        if data.description is not None:
            current_user.description = data.description
        if data.inn is not None:
            current_user.inn = data.inn
    else:
        if data.description is not None or data.inn is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Поля description и inn доступны только для организаций"
            )

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


async def get_my_complaints(
    session: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 20
) -> ComplaintList:
    """Пользователь смотрит свои жалобы"""

    query = select(Complaint).where(Complaint.complainant_id == current_user.id)

    total = await session.execute(
        select(func.count()).select_from(Complaint).where(Complaint.complainant_id == current_user.id)
    )
    total = total.scalar() or 0

    query = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    complaints = result.scalars().all()

    return ComplaintList(
        complaints=[ComplaintRead.model_validate(c) for c in complaints],
        total=total
    )
