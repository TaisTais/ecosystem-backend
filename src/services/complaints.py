from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from src.models.complaints import Complaint, TargetType, ComplaintStatus
from src.models.users import User, UserRole
from src.schemas.complaints import ComplaintCreate, ComplaintUpdate, ComplaintRead, ComplaintList
from src.services.events import delete_event
from src.services.feed import delete_post, delete_comment
from src.services.users import block_user


async def create_complaint(
    session: AsyncSession,
    complainant: User,
    data: ComplaintCreate
) -> Complaint:
    """Пользователь создаёт жалобу"""
    # Администраторы не могут подавать жалобы
    if complainant.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Администраторы не могут подавать жалобы"
        )

    # Модераторы могут жаловаться только на других модераторов
    if complainant.role == UserRole.MODERATOR:
        if data.target_type != TargetType.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Модераторы могут подавать жалобы только на других модераторов"
            )

        # Проверяем, что цель — именно модератор
        target_result = await session.execute(
            select(User).where(User.id == data.target_id)
        )
        target = target_result.scalar_one_or_none()

        if not target:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        if target.role != UserRole.MODERATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Модераторы могут подавать жалобы только на других модераторов"
            )

    # Обычные пользователи и организации (CITIZEN, ORGANIZATION)
    else:
        if data.target_type == TargetType.USER:
            # Не могут жаловаться на администраторов
            target_result = await session.execute(
                select(User).where(User.id == data.target_id)
            )
            target = target_result.scalar_one_or_none()

            if not target:
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            if target.role == UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Жалобы на администратора невозможны"
                )

    complaint = Complaint(
        complainant_id=complainant.id,
        target_type=data.target_type,
        target_id=data.target_id,
        comment=data.comment,
        status=ComplaintStatus.IN_PROGRESS,
        moderator_response=None
    )

    session.add(complaint)
    await session.commit()
    await session.refresh(complaint, ["complainant"])

    return complaint


async def get_complaints_list(
    session: AsyncSession,
    moderator: User,
    skip: int = 0,
    limit: int = 50,
    status: Optional[ComplaintStatus] = None,
    target_type: Optional[TargetType] = None  # ← новый фильтр
) -> ComplaintList:
    """Модератор получает список жалоб с фильтрами"""

    if moderator.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Нет прав доступа")

    query = select(Complaint).options(selectinload(Complaint.complainant))

    # Применяем фильтры
    if status:
        query = query.where(Complaint.status == status)

    if target_type:
        query = query.where(Complaint.target_type == target_type)

    # Общее количество жалоб с учётом фильтров
    total_query = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_query.scalar() or 0

    # Основной запрос с сортировкой и пагинацией
    query = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    complaints = result.scalars().all()

    return ComplaintList(
        complaints=[ComplaintRead.model_validate(c) for c in complaints],
        total=total
    )


async def review_complaint(
    session: AsyncSession,
    moderator: User,
    complaint_id: int,
    data: ComplaintUpdate
) -> Complaint:
    """Модератор или администратор обрабатывает жалобу"""

    if moderator.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Нет прав доступа")

    result = await session.execute(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(selectinload(Complaint.complainant))
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")

    if complaint.status != ComplaintStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Жалоба уже обработана")

    # === Новая логика обработки жалоб ===
    if moderator.role == UserRole.ADMIN:
        # Администратор может обрабатывать только жалобы на модераторов
        if complaint.target_type != TargetType.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Администратор может обрабатывать только жалобы на модераторов"
            )

        # Проверяем, что цель — действительно модератор
        target_result = await session.execute(
            select(User).where(User.id == complaint.target_id)
        )
        target_user = target_result.scalar_one_or_none()

        if target_user and target_user.role != UserRole.MODERATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Администратор может обрабатывать только жалобы на модераторов"
            )

    elif moderator.role == UserRole.MODERATOR:
        # Модератор может обрабатывать всё, кроме жалоб на модераторов
        if complaint.target_type == TargetType.USER:
            target_result = await session.execute(
                select(User).where(User.id == complaint.target_id)
            )
            target_user = target_result.scalar_one_or_none()

            if target_user and target_user.role == UserRole.MODERATOR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Модератор не может обрабатывать жалобы на других модераторов"
                )

    # === Обработка жалобы ===
    complaint.status = data.status
    if data.status == ComplaintStatus.APPROVED:
        try:
            if complaint.target_type == TargetType.USER:
                await block_user(
                    session=session,
                    user_id=complaint.target_id,
                    moderator=moderator,
                    reason=complaint.comment  # причина из жалобы
                )

            elif complaint.target_type == TargetType.CONTENT:
                await delete_post(
                    session=session,
                    post_id=complaint.target_id,
                    current_user=moderator,
                    reason=complaint.comment
                )

            elif complaint.target_type == TargetType.COMMENT:
                await delete_comment(
                    session=session,
                    comment_id=complaint.target_id,
                    current_user=moderator,
                    reason=complaint.comment
                )

            elif complaint.target_type == TargetType.EVENT:
                await delete_event(
                    session=session,
                    event_id=complaint.target_id,
                    reason=complaint.comment,
                    current_user=moderator
                )

        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=f"Не удалось выполнить действие по жалобе: {e.detail}"
            )
    complaint.moderator_id = moderator.id
    complaint.moderator_response = data.moderator_response
    complaint.moderated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(complaint)

    return complaint
