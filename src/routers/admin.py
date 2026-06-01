from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_admin
from src.database import get_session
from src.models.users import User
from src.schemas.admin import ModeratorCreate, ModeratorActionRead, ModeratorActionDetailRead
from src.schemas.users import UserRead
from src.services.admin import create_moderator, block_moderator, unblock_moderator, get_all_moderators, \
    get_moderator_detail

router = APIRouter(prefix="/admin", tags=["Администратор"])


@router.post("/new-moderator", response_model=UserRead, status_code=201, summary="Создать модератора")
async def create_moderator_endpoint(
    moderator_data: ModeratorCreate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Создать модератора"""
    return await create_moderator(session, current_admin, moderator_data)


@router.get("/moderators", response_model=List[ModeratorActionRead], summary="Получить данные о модераторах")
async def r_get_all_moderators(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Админ получает список всех модераторов + статистику"""
    return await get_all_moderators(session, current_admin, skip, limit)


@router.get("/moderators/{moderator_id}", response_model=List[ModeratorActionDetailRead], summary="Полная история действий модератора")
async def r_get_moderator_detail(
    moderator_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Админ просматривает полную историю модерации выбранного модератора"""
    return await get_moderator_detail(session, current_admin, moderator_id, skip, limit)


@router.delete("/moderators/{moderator_id}/block", response_model=dict, status_code=200, summary="Удалить модератора")
async def r_block_moderator(
    moderator_id: int,
    reason: Optional[str] = Query(None, description="Причина блокировки"),
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Удалить (заблокировать) модератора"""
    return await block_moderator(session, moderator_id, current_user, reason)


@router.post("/moderators/{moderator_id}/unblock", response_model=dict, summary="Восстановить модератора")
async def r_unblock_moderator(
    moderator_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Восстановить (разблокировать) модератора"""
    return await unblock_moderator(session, moderator_id, current_admin)
