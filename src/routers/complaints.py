from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional

from select import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_session
from src.models.users import User, UserRole
from src.models.complaints import ComplaintStatus, Complaint, TargetType
from src.schemas.complaints import (
    ComplaintCreate,
    ComplaintRead,
    ComplaintUpdate,
    ComplaintList, ComplaintDetailRead
)
from src.services.complaints import (
    create_complaint,
    get_complaints_list,
    review_complaint
)
from src.services.profile import get_my_complaints
from src.core.dependencies import get_current_user_by_token, get_current_moderator, get_current_moderator_or_admin

router = APIRouter(prefix="/complaints", tags=["Жалобы"])


@router.post("/", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED, summary="Создать жалобу")
async def create_new_complaint(
    data: ComplaintCreate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Создать жалобу

    Правила:
    - Жители и организации могут жаловаться на всё, кроме администратора.
    - Модераторы могут жаловаться только на других модераторов.
    - Администраторы не могут подавать жалобы.
    """
    return await create_complaint(session, current_user, data)


@router.get("/", response_model=ComplaintList)
async def get_all_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[ComplaintStatus] = Query(None, description="Фильтр по статусу"),
    target_type: Optional[TargetType] = Query(None, description="Фильтр по типу цели (USER, CONTENT, EVENT, COMMENT)"),
    moderator: User = Depends(get_current_moderator_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """Получить список всех жалоб с фильтрами"""
    return await get_complaints_list(
        session=session,
        moderator=moderator,
        skip=skip,
        limit=limit,
        status=status,
        target_type=target_type
    )


@router.get("/{complaint_id}", response_model=ComplaintDetailRead)
async def get_complaint_detail(
    complaint_id: int,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Получить детальную информацию о жалобе"""
    result = await session.execute(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(selectinload(Complaint.complainant))
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")

    if complaint.complainant_id != current_user.id and current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Нет прав доступа")

    return ComplaintDetailRead.model_validate(complaint)


@router.post("/{complaint_id}/review", response_model=ComplaintRead)
async def r_review_complaint(
    complaint_id: int,
    data: ComplaintUpdate,
    moderator: User = Depends(get_current_moderator_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """Модератор обрабатывает жалобу (одобряет или отклоняет)"""
    return await review_complaint(
        session=session,
        moderator=moderator,
        complaint_id=complaint_id,
        data=data
    )
