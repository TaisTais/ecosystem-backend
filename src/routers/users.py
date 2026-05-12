from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user
from src.database import get_session
from src.models import User
from src.schemas.users import UserCreate, UserRead, UserUpdate
from src.services.users import create_user, get_user_by_id, update_user

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить данные текущего пользователя"""
    return current_user


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """Регистрация нового пользователя"""
    return await create_user(session, user_data)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить пользователя по ID"""
    return await get_user_by_id(session, user_id)


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_data: UserUpdate,
    # current_user: User = Depends(get_current_user),  # позже
    session: AsyncSession = Depends(get_session)
):
    """Обновление своего профиля (пока без защиты)"""
    # Пока для теста используем ID = 1
    return await update_user(session, 1, user_data)
