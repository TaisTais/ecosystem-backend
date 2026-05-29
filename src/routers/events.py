from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.core.dependencies import get_current_user_by_token, get_current_moderator_or_admin
from src.database import get_session
from src.models.users import User
from src.schemas.events import (
    EventCreate, EventRead, EventCalendarRead, EventFilter,
    EventUpdate, EventApplicantCreate, EventParticipantCreate,
    EventApplicantRead, EventParticipantRead, MyEventsRead
)
from src.services.events import (
    create_event, get_events_calendar, get_event_by_id,
    get_my_events_grouped, update_event,
    apply_to_event, confirm_participation, delete_event
)

router = APIRouter(prefix="/events", tags=["События"])


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_new_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Создать новое мероприятие"""
    return await create_event(session, data, current_user)


@router.get("/", response_model=List[EventCalendarRead], summary="Посмотреть календарь событий")
async def r_get_calendar_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    is_online: Optional[bool] = Query(None),
    tag: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Получить список событий для календаря"""
    filters = EventFilter(
        start_date=start_date,
        end_date=end_date,
        is_online=is_online,
        tag=tag,
        skip=skip,
        limit=limit
    )
    return await get_events_calendar(session, filters)


@router.get("/my", response_model=MyEventsRead, summary="Мои события")
async def r_get_my_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Получить все мои события (организатор / участник / заявка)"""
    return await get_my_events_grouped(session, current_user, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=EventRead, summary="Подробнее о событии")
async def get_event_detail(
    event_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить подробную информацию о событии"""
    event = await get_event_by_id(session, event_id)
    return EventRead.model_validate(event)


@router.patch("/{event_id}", response_model=EventRead, summary="Редактировать событие")
async def r_update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Редактировать событие (организатор)"""
    return await update_event(session, event_id, data, current_user)


@router.delete("/{event_id}", status_code=status.HTTP_200_OK, summary="Удалить событие")
async def r_delete_event(
    event_id: int,
    reason: str = Query(..., description="Причина отмены"),
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Отменить событие"""
    return await delete_event(session, event_id, reason, current_user)


@router.post("/{event_id}/apply", response_model=EventApplicantRead, status_code=status.HTTP_201_CREATED, summary="Зарегистрирвоаться в событии")
async def r_apply_to_event(
    event_id: int,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Подать заявку на участие в событии"""
    return await apply_to_event(session, event_id, current_user)


@router.post("/{event_id}/participate", response_model=EventParticipantRead, status_code=status.HTTP_201_CREATED, summary="Подтвердить участие в событии")
async def r_confirm_participation(
    event_id: int,
    data: EventParticipantCreate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Подтвердить участие (загрузить доказательство)"""
    return await confirm_participation(session, event_id, data, current_user)
