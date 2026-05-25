from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user_by_token, get_current_moderator_or_admin
from src.database import get_session
from src.models.users import UserRole, User
from src.schemas.users import UserRead, UserListRead, UserPublicRead, UserPublicListRead
from src.services.users import get_user_by_id, get_users_list, block_user, unblock_user

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/{user_id}", summary="Получить данные пользователя по ID")
async def get_user_by_id_endpoint(
        user_id: int,
        current_user: User = Depends(get_current_user_by_token),
        session: AsyncSession = Depends(get_session)
):
    """Получить данные пользователя по ID.
    - Обычным пользователям — публичные данные
    - Модераторам и админам — расширенные данные"""

    user = await get_user_by_id(session, user_id)

    if user.id == current_user.id or current_user.role in [UserRole.MODERATOR, UserRole.ADMIN]:
        return UserRead.from_orm(user)
    return UserPublicRead.from_orm(user)


@router.get("/", summary="Получить список пользователей")
async def get_users_list_endpoint(
        role: Optional[UserRole] = Query(None, description="Фильтр по роли"),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        current_user: User = Depends(get_current_user_by_token),
        session: AsyncSession = Depends(get_session)
):
    """Получить список пользователей.
    - Для модераторов и администраторов — расширенная информация
    - Для обычных пользователей — только публичная информация"""
    users = await get_users_list(
        session=session,
        role=role,
        skip=skip,
        limit=limit
    )

    if current_user.role in [UserRole.MODERATOR, UserRole.ADMIN]:
        return [UserListRead.from_orm(user) for user in users]
    return [UserPublicListRead.from_orm(user) for user in users]


@router.post("/{user_id}/block", response_model=UserRead, summary="Заблокировать пользователя (для модераторов/админов)")
async def r_block_user(
    user_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_moderator_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """Заблокировать пользователя (модератор/админ)"""
    return await block_user(session, user_id, current_user, reason)


@router.post("/{user_id}/unblock", response_model=UserRead, summary="Разблокировать пользователя (для модераторов/админов)")
async def r_unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_moderator_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """Разблокировать пользователя (модератор/админ)"""
    return await unblock_user(session, user_id, current_user)