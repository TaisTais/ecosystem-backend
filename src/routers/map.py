from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.dependencies import get_current_user_by_token, get_current_citizen
from src.database import get_session
from src.models import User
from src.schemas.map import (
    EcoPointCreate,
    EcoPointRead,
    EcoPointStatusCreate,
    EcoPointReviewCreate,
    EcoPointReviewRead,
    EcoPointFilter,
    EcoPointListRead,
    EcoPointUpdate, VisitCreate,
)
from src.schemas.moderation import ModerationRecordRead
from src.services.map import (
    get_ecopoints,
    get_ecopoint_detail,
    add_status_to_ecopoint,
    add_review_to_ecopoint, request_create_ecopoint, request_update_ecopoint, request_create_visit,
)

router = APIRouter(prefix="/map", tags=["Карта"])


@router.post("/", summary="Создать эко-точку", response_model=ModerationRecordRead, status_code=201)
async def r_request_create_ecopoint(
    data: EcoPointCreate,
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Создать точку (житель)"""
    return await request_create_ecopoint(session, data, current_user)


@router.get("/", summary="Получить список эко-точек с фильтрами", response_model=List[EcoPointListRead])
async def r_get_ecopoints(
    filters: EcoPointFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """Получить все точки (без ограничений)"""
    return await get_ecopoints(session, filters, skip, limit)


@router.get("/{ecopoint_id}", summary="Получить эко-точку по id", response_model=EcoPointRead)
async def r_get_ecopoint_detail(ecopoint_id: int, session: AsyncSession = Depends(get_session)
):
    """Получить одну точку (без ограничений)"""
    return await get_ecopoint_detail(session, ecopoint_id)


@router.post("/{ecopoint_id}/status", summary="Поставить статус эко-точке", response_model=dict,
             status_code=status.HTTP_201_CREATED)
async def r_add_status_to_ecopoint(
    ecopoint_id: int,
    status_data: EcoPointStatusCreate,
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Поставить статус точке (житель)"""
    await add_status_to_ecopoint(session, ecopoint_id, status_data, current_user)
    return {"message": "Статус успешно добавлен"}


@router.post("/{ecopoint_id}/review", summary="Оставить отзыв эко-точке",
             response_model=EcoPointReviewRead,
             status_code=status.HTTP_201_CREATED)
async def r_add_review_to_ecopoint(
    ecopoint_id: int,
    review_data: EcoPointReviewCreate,
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Оставить отзыв к точке (житель)"""
    review = await add_review_to_ecopoint(session, ecopoint_id, review_data, current_user)
    return review


@router.patch("/{ecopoint_id}", summary="Обновить данные эко-точки", response_model=ModerationRecordRead)
async def r_request_update_ecopoint(
    ecopoint_id: int,
    update_data: EcoPointUpdate,
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Обновить данные эко-точки (житель)"""
    return await request_update_ecopoint(session, ecopoint_id, update_data, current_user)


@router.post("/visits", summary="Отметить посещение эко-точки", response_model=ModerationRecordRead, status_code=201)
async def r_request_create_visit(
    data: VisitCreate,
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Отправить доказательство посещения эко-точки (житель)"""
    return await request_create_visit(session, data, current_user)
