from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from src.models.events import Event, EventStatus
from src.models.users import User
from src.schemas.events import (
    EventCreate, EventRead, EventCalendarRead,
    EventFilter, EventUpdate
)


async def create_event(
    session: AsyncSession,
    data: EventCreate,
    current_user: User
) -> Event:
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

    # Добавляем организатора
    new_event.organizers.append(current_user)

    session.add(new_event)
    await session.commit()
    await session.refresh(new_event)

    return new_event


async def get_events_calendar(
    session: AsyncSession,
    filters: EventFilter
) -> List[EventCalendarRead]:
    """Получить события для календаря"""

    query = select(Event).where(Event.status == EventStatus.ACTIVE)

    if filters.start_date:
        query = query.where(Event.start_datetime >= filters.start_date)
    if filters.end_date:
        query = query.where(Event.start_datetime <= filters.end_date)
    if filters.is_online is not None:
        query = query.where(Event.is_online == filters.is_online)
    if filters.tag:
        query = query.where(Event.tags.ilike(f"%{filters.tag}%"))

    query = query.order_by(Event.start_datetime.asc())
    query = query.offset(filters.skip).limit(filters.limit)

    result = await session.execute(query)
    events = result.scalars().all()

    return [EventCalendarRead.model_validate(event) for event in events]
