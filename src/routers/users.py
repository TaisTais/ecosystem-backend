from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user
from src.database import get_session
from src.models import User
from src.schemas.users import UserCreate, UserRead, UserUpdate
from src.services.users import create_user, get_user_by_id, update_user

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", summary="Посмотреть данные своего аккаунта", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить данные своего аккаунта (только авторизованным пользователям)"""
    return current_user


@router.get("/{user_id}", summary="Получить данные аккаунта по id", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить пользователя по ID"""
    return await get_user_by_id(session, user_id)


@router.patch("/me", summary="Обновить данные своего аккаунта", response_model=UserRead)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Обновление своего профиля"""
    if not user_data.model_fields_set:  # если ничего не передали
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не передано ни одного поля для обновления"
        )
    return await update_user(session, current_user, user_data)
