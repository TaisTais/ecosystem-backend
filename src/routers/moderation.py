from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user_by_token, get_current_citizen, get_current_moderator_or_admin, \
    get_current_moderator
from src.database import get_session
from src.models import User, ModerationStatus
from src.models.achievements import ActionType
from src.schemas.moderation import ModerationRecordDetailRead, ModerationDecisionRead, ModerationRecordRead, \
    ModerationDecisionCreate
from src.services.moderation import approve_moderation, get_moderations, reject_moderation

router = APIRouter(prefix="/moderation", tags=["Модерация"])


@router.get("/", summary="Получить список заявок на модерацию", response_model=List[ModerationRecordDetailRead])
async def get_moderations_list(
    action_type: Optional[ActionType] = Query(None, description="Тип действия"),
    status: Optional[ModerationStatus] = Query(None, description="Статус заявки"),
    moderator_id: Optional[int] = Query(None, description="Кто обрабатывал"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_moderator_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """Получить список заявок на модерацию (только для модераторов и администраторов)"""

    moderations = await get_moderations(
        session=session,
        action_type=action_type,
        status=status,
        moderator_id=moderator_id,
        skip=skip,
        limit=limit
    )

    return moderations


@router.post("/{moderation_id}/approve", summary="Одобрить заявку", response_model=ModerationDecisionRead)
async def approve_moderation_request(
    moderation_id: int,
    decision: ModerationDecisionCreate,
    current_user: User = Depends(get_current_moderator),
    session: AsyncSession = Depends(get_session)
):
    """Модератор или администратор одобряет заявку"""
    return await approve_moderation(session, moderation_id, current_user, decision)


@router.post("/{moderation_id}/reject", summary="Отклонить заявку", response_model=ModerationDecisionRead)
async def reject_moderation_request(
    moderation_id: int,
    decision: ModerationDecisionCreate,
    current_user: User = Depends(get_current_moderator),
    session: AsyncSession = Depends(get_session)
):
    """Модератор или администратор отклоняет заявку"""
    return await reject_moderation(session, moderation_id, current_user, decision)
