from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.dependencies import get_current_user_by_token, get_current_citizen, get_current_moderator
from src.database import get_session
from src.models.users import User
from src.schemas.moderation import ModerationRecordRead, ModerationRecordDetailRead
from src.schemas.users import UserRead, UserUpdate
from src.services.profile import update_current_user, get_my_moderations, get_my_moderation_actions

router = APIRouter(prefix="/me", tags=["Профиль"])


@router.get("/", summary="Посмотреть свои данные", response_model=UserRead)
async def r_get_current_user(current_user: User = Depends(get_current_user_by_token)):
    """Получить данные своего аккаунта (авторизованные)"""
    return current_user


@router.get("/moderations", summary="Посмотреть свои заявки на модерацию", response_model=List[ModerationRecordRead])
async def r_get_my_moderations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_citizen),
    session: AsyncSession = Depends(get_session)
):
    """Получить список своих заявок на модерацию (жители)"""
    return await get_my_moderations(
        session=session,
        current_user=current_user,
        skip=skip,
        limit=limit
    )


@router.get("/moderation-actions", response_model=List[ModerationRecordDetailRead], summary="Мои действия по модерации (для модераторов)")
async def get_my_moderation_actions_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_moderator),
    session: AsyncSession = Depends(get_session)
):
    """Модератор смотрит историю своих модераций"""
    return await get_my_moderation_actions(
        session=session,
        current_moderator=current_user,
        skip=skip,
        limit=limit
    )


@router.patch("/update", summary="Обновить данные своего аккаунта", response_model=UserRead)
async def r_update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Обновление своего профиля"""
    if not user_data.model_fields_set:  # если ничего не передали
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не передано ни одного поля для обновления"
        )
    return await update_current_user(session, current_user, user_data)
