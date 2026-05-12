from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.users import UserCreate, UserLogin, Token, UserRead
from src.services.auth import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """Регистрация нового пользователя"""
    return await register_user(session, user_data)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """Авторизация пользователя и получение JWT-токена"""
    return await authenticate_user(session, login_data)
