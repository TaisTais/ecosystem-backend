from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from src.models import User
from src.models.map import EcoPoint, Status, Review
from src.schemas.map import (
    EcoPointCreate,
    EcoPointRead,
    EcoPointStatusCreate,
    EcoPointReviewCreate,
    EcoPointFilter,
    EcoPointStatusRead,
    EcoPointMostConfirmedStatusRead
)


async def create_ecopoint(session: AsyncSession, data: EcoPointCreate, current_user: User) -> EcoPoint:
    """Создание новой эко-точки авторизованным пользователем"""

    new_point = EcoPoint(
        name=data.name,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        type=data.type,
        description=data.description,
        working_hours=data.working_hours,
        source="local",
        created_by_id=current_user.id
    )

    session.add(new_point)
    await session.commit()
    await session.refresh(new_point)

    return new_point


async def get_most_confirmed_status(session: AsyncSession, ecopoint_id: int) -> EcoPointMostConfirmedStatusRead:
    """Возвращает самый популярный статус точки (для списка/карты)"""

    query = select(
        Status.status,
        func.count(Status.id).label("confirmed_by"),
        func.max(Status.created_at).label("last_updated_at")
    ).where(
        Status.ecopoint_id == ecopoint_id
    ).group_by(
        Status.status
    ).order_by(
        func.count(Status.id).desc()
    ).limit(1)

    result = await session.execute(query)
    row = result.first()

    if not row:
        return EcoPointMostConfirmedStatusRead(most_confirmed_status=None)

    status_read = EcoPointStatusRead(
        status=row.status,
        confirmed_by=row.confirmed_by or 0,
        last_updated_at=row.last_updated_at
    )

    return EcoPointMostConfirmedStatusRead(most_confirmed_status=status_read)


async def get_ecopoints(
        session: AsyncSession,
        filters: EcoPointFilter,
        skip: int = 0,
        limit: int = 1000
) -> List[EcoPoint]:
    """Просмотр точек на карте"""

    query = select(EcoPoint)

    if filters.type:
        query = query.where(EcoPoint.type == filters.type)

    # Фильтр по координатам (для области карты)
    if filters.min_latitude is not None:
        query = query.where(EcoPoint.latitude >= filters.min_latitude)
    if filters.max_latitude is not None:
        query = query.where(EcoPoint.latitude <= filters.max_latitude)
    if filters.min_longitude is not None:
        query = query.where(EcoPoint.longitude >= filters.min_longitude)
    if filters.max_longitude is not None:
        query = query.where(EcoPoint.longitude <= filters.max_longitude)

    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    points = list(result.scalars().all())
    for point in points:
        most_status_wrapper = await get_most_confirmed_status(session, point.id)
        point.most_confirmed_status = most_status_wrapper
    return points


async def get_ecopoint_detail(session: AsyncSession, ecopoint_id: int) -> EcoPoint:
    """Получить полную информацию об одной эко-точке"""
    result = await session.execute(
        select(EcoPoint)
        .options(
            selectinload(EcoPoint.reviews),  # загружаем отзывы
            selectinload(EcoPoint.statuses)  # загружаем все статусы
        )
        .where(EcoPoint.id == ecopoint_id)
    )

    point = result.scalar_one_or_none()

    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Эко-точка не найдена"
        )
    return point


async def create_status(session: AsyncSession, ecopoint_id: int, status_data: EcoPointStatusCreate, user_id: int):
    """Пользователь ставит статус точки"""
    # Пока простая реализация (позже добавим ModerationRecord)
    new_status = Status(
        ecopoint_id=ecopoint_id,
        user_id=user_id,
        status=status_data.status
    )

    session.add(new_status)
    await session.commit()
    await session.refresh(new_status)
    return new_status


async def create_review(session: AsyncSession, ecopoint_id: int, review_data: EcoPointReviewCreate, user_id: int) \
        -> Review:
    """Создание отзыва к эко-точке"""
    new_review = Review(
        ecopoint_id=ecopoint_id,
        user_id=user_id,
        comment=review_data.comment,
        photo_url=review_data.photo_url,
        status=review_data.status
    )

    session.add(new_review)
    await session.commit()
    await session.refresh(new_review)
    return new_review
