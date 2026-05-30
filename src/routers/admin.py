from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_admin
from src.database import get_session
from src.models.users import User
from src.schemas.admin import ModeratorCreate
from src.schemas.users import UserRead
from src.services.admin import create_moderator

router = APIRouter(prefix="/admin", tags=["Администратор"])


@router.post("/moderators", response_model=UserRead, status_code=201, summary="Создать модератора")
async def create_moderator_endpoint(
    moderator_data: ModeratorCreate,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Создать модератора (только админ)"""
    return await create_moderator(session, current_user, moderator_data)
