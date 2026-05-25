from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.users import User, UserRole
from src.core.security import decode_access_token
from src.services.users import get_user_by_id

security = HTTPBearer()  # ← ожидает токен в заголовке Authorization: Bearer ...


async def get_current_user_by_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        session: AsyncSession = Depends(get_session)
) -> User:
    """Проверка по JWT токену, что пользователь авторизован"""
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен"
            )

        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден"
            )

        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь заблокирован"
            )

        return user

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истёкший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== РОЛЕВЫЕ ЗАВИСИМОСТИ ====================
async def get_current_citizen(
    current_user: User = Depends(get_current_user_by_token)
) -> User:
    """Только Житель"""
    if current_user.role != UserRole.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данное действие доступно только жителям"
        )
    return current_user


async def get_current_organization(
    current_user: User = Depends(get_current_user_by_token)
) -> User:
    """Только Организация"""
    if current_user.role != UserRole.ORGANIZATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данное действие доступно только организациям"
        )
    return current_user


async def get_current_citizen_or_organization(
    current_user: User = Depends(get_current_user_by_token)
) -> User:
    """Житель или Организация"""
    if current_user.role not in [UserRole.CITIZEN, UserRole.ORGANIZATION]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данное действие доступно только жителям и организациям"
        )
    return current_user


async def get_current_moderator(
    current_user: User = Depends(get_current_user_by_token)
) -> User:
    """Только Модератор"""
    if current_user.role != UserRole.MODERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данное действие доступно только модераторам"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user_by_token)
) -> User:
    """Только Администратор"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данное действие доступно только администраторам"
        )
    return current_user


async def get_current_moderator_or_admin(
    current_user: User = Depends(get_current_user_by_token)
) -> User:
    """Модератор или Администратор"""
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данное действие доступно только модераторам и администраторам"
        )
    return current_user
