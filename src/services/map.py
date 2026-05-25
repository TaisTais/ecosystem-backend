from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from src.models import User
from src.models.achievements import ActionType
from src.models.map import EcoPoint, Status, Review, Visit, EcoPointCategory
from src.models.moderation import ModerationRecord, ModerationStatus
from src.schemas.map import (
    EcoPointCreate,
    EcoPointStatusCreate,
    EcoPointReviewCreate,
    EcoPointFilter,
    EcoPointStatusRead,
    EcoPointMostConfirmedStatusRead, EcoPointUpdate, VisitCreate
)


async def request_create_ecopoint(
    session: AsyncSession,
    data: EcoPointCreate,
    current_user: User
) -> ModerationRecord:
    """Подача запроса на создание новой эко-точки (через модерацию)"""
    moderation = ModerationRecord(
        action_type="add_point",
        action_id=0,
        user_id=current_user.id,
        new_data=data.model_dump(),
        status="pending"
    )

    session.add(moderation)
    await session.commit()
    await session.refresh(moderation)
    return moderation


async def request_update_ecopoint(
    session: AsyncSession,
    ecopoint_id: int,
    update_data: EcoPointUpdate,
    current_user: User
) -> ModerationRecord:
    """Подача запроса на обновление данных эко-точки (через модерацию)"""

    # Проверяем существование точки
    result = await session.execute(
        select(EcoPoint).where(EcoPoint.id == ecopoint_id)
    )
    point = result.scalar_one_or_none()

    if not point:
        raise HTTPException(status_code=404, detail="Эко-точка не найдена")

    old_data = {
        "name": point.name,
        "address": point.address,
        "latitude": point.latitude,
        "longitude": point.longitude,
        "type": point.type,
        "description": point.description,
        "working_hours": point.working_hours,
    }

    moderation = ModerationRecord(
        action_type="update_point",
        action_id=ecopoint_id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data.model_dump(exclude_unset=True),
        status="pending"
    )

    session.add(moderation)
    await session.commit()
    await session.refresh(moderation)

    return moderation


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


async def get_ecopoints(session: AsyncSession, filters: EcoPointFilter, skip: int = 0, limit: int = 1000) -> List[EcoPoint]:
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


async def get_ecopoint_by_id(session: AsyncSession, ecopoint_id: int) -> EcoPoint:
    """Получить эко-точку по ID или вернуть 404"""

    result = await session.execute(
        select(EcoPoint).where(EcoPoint.id == ecopoint_id)
    )

    point = result.scalar_one_or_none()

    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Эко-точка с id={ecopoint_id} не найдена"
        )

    return point


async def add_status_to_ecopoint(session: AsyncSession, ecopoint_id: int, status_data: EcoPointStatusCreate, current_user: User):
    """Пользователь ставит статус точки"""

    await get_ecopoint_by_id(session, ecopoint_id)

    new_status = Status(
        ecopoint_id=ecopoint_id,
        user_id=current_user.id,
        status=status_data.status
    )

    session.add(new_status)
    await session.commit()
    await session.refresh(new_status)

    return new_status


async def add_review_to_ecopoint(session: AsyncSession, ecopoint_id: int, review_data: EcoPointReviewCreate, current_user: User) -> Review:
    """Оставить отзыв к точке"""

    await get_ecopoint_by_id(session, ecopoint_id)

    new_review = Review(
        ecopoint_id=ecopoint_id,
        user_id=current_user.id,
        comment=review_data.comment,
        photo_url=review_data.photo_url
    )

    session.add(new_review)
    await session.commit()
    await session.refresh(new_review)

    return new_review


async def request_create_visit(
    session: AsyncSession,
    data: VisitCreate,
    current_user: User
) -> ModerationRecord:
    """Пользователь отправляет доказательство посещения эко-точки"""

    # Проверяем точку
    point_result = await session.execute(
        select(EcoPoint).where(EcoPoint.id == data.ecopoint_id)
    )
    point = point_result.scalar_one_or_none()

    if not point:
        raise HTTPException(status_code=404, detail="Эко-точка не найдена")

    # Создаём посещение
    visit = Visit(
        user_id=current_user.id,
        ecopoint_id=data.ecopoint_id,
        proof_photo_url=data.proof_photo_url,
        visited_at=data.visited_at,
        comment=data.comment,
    )
    session.add(visit)
    await session.commit()
    await session.refresh(visit)

    # Определяем тип достижения
    if point.type in [EcoPointCategory.PLASTIC, EcoPointCategory.GLASS, EcoPointCategory.PAPER,
                      EcoPointCategory.METAL, EcoPointCategory.BATTERIES, EcoPointCategory.ELECTRONICS]:
        action_type = ActionType.VISIT_RECYCLING_POINT
    else:
        action_type = ActionType.VISIT_OWN_TARA_POINT

    # Создаём запись модерации
    moderation = ModerationRecord(
        action_type=action_type,
        action_id=visit.id,  # ссылка на Visit
        user_id=current_user.id,
        new_data={
            "ecopoint_id": point.id,
            "ecopoint_name": point.name,
            "photo_url": visit.proof_photo_url,
            "visited_at": visit.visited_at.isoformat()
        },
        status=ModerationStatus.PENDING
    )
    session.add(moderation)
    await session.commit()
    await session.refresh(moderation)
    return moderation
