from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from sqlalchemy.orm import Query

from src.database import get_session
from src.schemas.map import (
    EcoPointCreate,
    EcoPointRead,
    EcoPointUpdate,
    EcoPointStatusCreate,
    EcoPointReviewCreate,
    EcoPointReviewRead, EcoPointFilter
)
from src.services.map import (
    create_ecopoint,
    get_ecopoints_with_filters,
    get_ecopoint_by_id,
)

router = APIRouter(prefix="/map", tags=["Карта"])


@router.post("/", response_model=EcoPointRead, status_code=status.HTTP_201_CREATED)
async def add_ecopoint(
    data: EcoPointCreate,
    session: AsyncSession = Depends(get_session),
    # current_user: User = Depends(get_current_user)  # позже
):
    """Добавить новую эко-точку"""
    # Пока используем ID = 1 для теста
    return await create_ecopoint(session, data, current_user_id=1)


@router.get("/", response_model=List[EcoPointRead])
async def get_map_points(
    filters: EcoPointFilter = Depends(),   # ← Важная строка!
    limit: int = Query(800, ge=1, le=1500),  # разумный максимум
    skip: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    """Use Case: просмотр точек на карте"""
    return await get_ecopoints_with_filters(
        session=session,
        filters=filters,
        skip=skip,
        limit=limit
    )


@router.get("/{ecopoint_id}", response_model=EcoPointRead)
async def get_ecopoint(
    ecopoint_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить одну точку"""
    return await get_ecopoint_by_id(session, ecopoint_id)


@router.patch("/{ecopoint_id}/status")
async def update_status(
    ecopoint_id: int,
    status_data: EcoPointStatusUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Поставить статус точки (работает / закрыто)"""
    # Реализуем позже
    return {"message": "Статус обновлён"}
