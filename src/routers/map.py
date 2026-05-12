from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.dependencies import get_current_user, get_current_citizen
from src.database import get_session
from src.models import User
from src.schemas.map import (
    EcoPointCreate,
    EcoPointRead,
    EcoPointStatusCreate,
    EcoPointReviewCreate,
    EcoPointReviewRead,
    EcoPointFilter, EcoPointListRead,
)
from src.services.map import (
    create_ecopoint,
    get_ecopoints,
    get_ecopoint_detail,
)

router = APIRouter(prefix="/map", tags=["Карта"])


@router.post("/", summary="Создать эко-точку", response_model=EcoPointRead, status_code=status.HTTP_201_CREATED)
async def r_create_ecopoint(
    data: EcoPointCreate,
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Создать точку (только житель)"""
    return await create_ecopoint(session, data, current_user)


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


