from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from src.models.map import EcoPoint, Status, Review
from src.schemas.map import (
    EcoPointCreate,
    EcoPointRead,
    EcoPointUpdate,
    EcoPointStatusCreate,
    EcoPointReviewCreate, EcoPointFilter
)


async def create_ecopoint(
    session: AsyncSession,
    data: EcoPointCreate,
    current_user_id: int
) -> EcoPoint:
    """Создание новой эко-точки"""
    new_point = EcoPoint(
        **data.model_dump(),
        created_by_id=current_user_id,
        source="local"
    )

    session.add(new_point)
    await session.commit()
    await session.refresh(new_point)
    return new_point


async def get_ecopoints_with_filters(
        session: AsyncSession,
        filters: EcoPointFilter,
        skip: int = 0,
        limit: int = 1000
) -> List[EcoPoint]:
    """Use Case: просмотр точек на карте"""

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
    return list(result.scalars().all())


async def get_ecopoint_by_id(session: AsyncSession, ecopoint_id: int) -> EcoPoint:
    """Получить одну точку по ID"""
    result = await session.execute(
        select(EcoPoint).where(EcoPoint.id == ecopoint_id)
    )
    point = result.scalar_one_or_none()

    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Эко-точка не найдена"
        )
    return point


async def create_status(
    session: AsyncSession,
    ecopoint_id: int,
    status_data: EcoPointStatusCreate,
    user_id: int
):
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


async def create_review(
    session: AsyncSession,
    ecopoint_id: int,
    review_data: EcoPointReviewCreate,
    user_id: int
) -> Review:
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
