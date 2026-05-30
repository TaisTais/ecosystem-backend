from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from src.models.events import Event, EventStatus, EventParticipant, EventApplicant
from src.models.users import User, UserRole
from src.schemas.events import (
    EventCreate, EventRead, EventCalendarRead,
    EventFilter, EventUpdate, EventParticipantRead, EventParticipantCreate, EventApplicantRead, MyEventsRead,
    OrganizerInfo
)
from src.services.utils import normalize_tags


async def create_event(session: AsyncSession, data: EventCreate, current_user: User) -> EventRead:
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
        tags=normalize_tags(data.tags),  # используем нормализацию как в постах
        status=EventStatus.ACTIVE
    )

    # Добавляем организатора
    new_event.organizers.append(current_user)

    session.add(new_event)
    await session.commit()
    await session.refresh(new_event, ["organizers"])

    # Ручное формирование ответа
    return EventRead(
        id=new_event.id,
        title=new_event.title,
        description=new_event.description,
        start_datetime=new_event.start_datetime,
        end_datetime=new_event.end_datetime,
        status=new_event.status,
        is_online=new_event.is_online,
        address=new_event.address,
        meeting_link=new_event.meeting_link,
        max_participants=new_event.max_participants,
        tags=[tag.strip() for tag in new_event.tags.split(',')] if new_event.tags else [],
        created_at=new_event.created_at,
        organizer_id=current_user.id,
        organizer_name=current_user.name,
        organizer_role=current_user.role.value,
        applicants_count=0,
        participants_count=0,
        is_user_applicant=False
    )


async def get_events_calendar(session: AsyncSession, filters: EventFilter) -> List[EventCalendarRead]:
    """Получить события для календаря и списка"""

    query = select(Event).where(Event.status == EventStatus.ACTIVE)

    if filters.start_date:
        query = query.where(Event.start_datetime >= filters.start_date)
    if filters.end_date:
        query = query.where(Event.start_datetime <= filters.end_date)
    if filters.is_online is not None:
        query = query.where(Event.is_online == filters.is_online)
    if filters.status:
        query = query.where(Event.status == filters.status)

    query = query.options(selectinload(Event.organizers))
    query = query.order_by(Event.start_datetime.asc())
    query = query.offset(filters.skip).limit(filters.limit)

    result = await session.execute(query)
    events = result.scalars().all()

    response = []
    for event in events:
        response.append(EventCalendarRead(
            id=event.id,
            title=event.title,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            is_online=event.is_online,
            status=event.status,
            max_participants=event.max_participants,
            participants_count=len(event.participants),
        ))

    return response


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

    changing_datetime = False
    if data.start_datetime is not None or data.end_datetime is not None:
        changing_datetime = True

    if changing_datetime:
        days_until_event = (event.start_datetime - datetime.now(timezone.utc)).days
        if days_until_event < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Изменять дату и время события можно не позднее чем за 2 дня до начала"
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if key == "tags":
                value = normalize_tags(value)  # ← КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ
            setattr(event, key, value)

    await session.commit()
    await session.refresh(event, ["organizers"])
    return event


async def delete_event(session: AsyncSession, event_id: int, reason: str, current_user: User) -> dict:
    """Отмена (удаление) события"""
    result = await session.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    # Проверка прав
    is_organizer = any(org.id == current_user.id for org in event.organizers)
    if not is_organizer and current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Нет прав на отмену события")

    # Мягкое удаление
    event.status = EventStatus.CANCELLED
    event.is_deleted = True
    event.deleted_at = datetime.now(timezone.utc)
    event.deleted_by = current_user.id
    if reason:
        event.deleted_reason = reason

    await session.commit()

    return {
        "success": True,
        "message": "Событие успешно отменено",
        "event_id": event_id,
        "status": event.status.value
    }


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

    return EventApplicantRead(
        user_id=current_user.id,
        user_name=current_user.name,
        applied_at=application.applied_at
    )


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

    existing = await session.execute(
        select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.participant_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже подтвердили участие в этом событии")

    participation = EventParticipant(
        event_id=event_id,
        participant_id=current_user.id,
        proof_photo_url=data.proof_photo_url,
        comment=data.comment
    )

    session.add(participation)
    await session.commit()
    await session.refresh(participation)

    return EventParticipantRead(
        user_id=current_user.id,
        user_name=current_user.name,
        confirmed_at=participation.confirmed_at
    )
