from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from src.models.events import Event, EventStatus, EventParticipant, EventApplicant
from src.models.users import User
from src.schemas.events import (
    EventCreate, EventRead, EventCalendarRead,
    EventFilter, EventUpdate, EventParticipantRead, EventParticipantCreate, EventApplicantRead, MyEventsRead
)


async def create_event(session: AsyncSession, data: EventCreate, current_user: User) -> Event:
    """Создание нового мероприятия (организация или житель)"""

    new_event = Event(
        title=data.title,
        description=data.description,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        is_online=data.is_online,
        address=data.address,
        meeting_link=data.meeting_link,
        max_participants=data.max_participants,
        tags=",".join(data.tags) if data.tags else None,
        status=EventStatus.ACTIVE
    )

    new_event.organizers.append(current_user)
    session.add(new_event)
    await session.commit()
    await session.refresh(new_event, ["organizers"])
    return new_event


async def get_events_calendar(session: AsyncSession, filters: EventFilter) -> List[EventCalendarRead]:
    """Получить события для календаря и списка"""

    query = select(Event).where(Event.status == EventStatus.ACTIVE)

    if filters.start_date:
        query = query.where(Event.start_datetime >= filters.start_date)
    if filters.end_date:
        query = query.where(Event.start_datetime <= filters.end_date)
    if filters.is_online is not None:
        query = query.where(Event.is_online == filters.is_online)
    if filters.tag:
        query = query.where(Event.tags.ilike(f"%{filters.tag}%"))
    if filters.status:
        query = query.where(Event.status == filters.status)

    query = query.options(selectinload(Event.organizers))
    query = query.order_by(Event.start_datetime.asc())
    query = query.offset(filters.skip).limit(filters.limit)

    result = await session.execute(query)
    events = result.scalars().all()
    return [EventCalendarRead.model_validate(event) for event in events]


async def get_event_by_id(session: AsyncSession, event_id: int) -> Event:
    """Получить одно событие по ID (внутренняя функция)"""
    result = await session.execute(
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.organizers))
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено"
        )
    return event


async def get_my_events_grouped(session: AsyncSession, current_user: User, skip: int = 0, limit: int = 20) -> MyEventsRead:
    """Возвращает события пользователя, разделённые по его ролям"""

    # 1. Как организатор
    organizer_query = select(Event).where(
        Event.organizers.any(id=current_user.id)
    ).options(selectinload(Event.organizers))

    # 2. Как подтверждённый участник
    participant_query = select(Event).join(
        EventParticipant, EventParticipant.event_id == Event.id
    ).where(
        EventParticipant.participant_id == current_user.id
    ).options(selectinload(Event.organizers))

    # 3. Как applicant (подал заявку)
    applicant_query = select(Event).join(
        EventApplicant, EventApplicant.event_id == Event.id
    ).where(
        EventApplicant.applicant_id == current_user.id
    ).options(selectinload(Event.organizers))

    # Выполняем запросы
    org_result = await session.execute(organizer_query.offset(skip).limit(limit))
    part_result = await session.execute(participant_query.offset(skip).limit(limit))
    app_result = await session.execute(applicant_query.offset(skip).limit(limit))

    return MyEventsRead(
        as_organizer=[EventRead.model_validate(e) for e in org_result.scalars().all()],
        as_participant=[EventRead.model_validate(e) for e in part_result.scalars().all()],
        as_applicant=[EventRead.model_validate(e) for e in app_result.scalars().all()]
    )


async def update_event(session: AsyncSession, event_id: int, data: EventUpdate, current_user: User) -> Event:
    """Редактирование события"""
    event = await get_event_by_id(session, event_id)

    is_organizer = any(org.id == current_user.id for org in event.organizers)
    if not is_organizer:
        raise HTTPException(status_code=403, detail="Нет прав на редактирование")

        # Проверка времени: нельзя менять дату/время события менее чем за 2 дня
    if event.start_datetime:
        days_until_event = (event.start_datetime - datetime.now(timezone.utc)).days
        if days_until_event < 2 and (data.start_datetime or data.end_datetime):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Изменять дату и время события можно не позднее чем за 2 дня до начала"
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(event, key, value)

    await session.commit()
    await session.refresh(event, ["organizers"])
    return event


async def delete_event(
    session: AsyncSession,
    event_id: int,
    reason: str,

    current_user: User
) -> Event:
    """Отмена события"""
    event = await get_event_by_id(session, event_id)

    is_organizer = any(org.id == current_user.id for org in event.organizers)
    if not is_organizer and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(status_code=403, detail="Нет прав на отмену события")

    event.status = EventStatus.CANCELLED
    # Можно добавить поле cancel_reason в модель, если нужно

    await session.commit()
    await session.refresh(event)
    return event


async def apply_to_event(
    session: AsyncSession,
    event_id: int,
    current_user: User
) -> EventApplicantRead:
    """Подать заявку на участие"""
    event = await get_event_by_id(session, event_id)

    # Проверка, не подал ли уже заявку
    existing = await session.execute(
        select(EventApplicant).where(
            EventApplicant.event_id == event_id,
            EventApplicant.applicant_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже подали заявку на это событие")

    application = EventApplicant(
        event_id=event_id,
        applicant_id=current_user.id
    )

    session.add(application)
    await session.commit()
    await session.refresh(application)

    return EventApplicantRead.model_validate(application)


async def confirm_participation(
    session: AsyncSession,
    event_id: int,
    data: EventParticipantCreate,
    current_user: User
) -> EventParticipantRead:
    """Подтвердить участие (загрузить доказательство)"""

    applicant_result = await session.execute(
        select(EventApplicant).where(
            EventApplicant.event_id == event_id,
            EventApplicant.applicant_id == current_user.id
        )
    )
    if not applicant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы не подавали заявку на это событие"
        )

    participation = EventParticipant(
        event_id=event_id,
        participant_id=current_user.id,
        proof_photo_url=data.proof_photo_url,
        comment=data.comment
    )

    session.add(participation)
    await session.commit()
    await session.refresh(participation)

    return EventParticipantRead.model_validate(participation)
