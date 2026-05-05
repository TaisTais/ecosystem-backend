from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.models.events import Event
from src.schemas.events import EventFilter
from src.services.utils import normalize_tags

async def get_events_calendar(
        session: AsyncSession,
        filters: EventFilter,
        skip: int = 0,
        limit: int = 50
) -> List[Event]:
    """Получить события для календаря с фильтрами"""

    query = select(Event)

    # Фильтр по датам
    if filters.start_date:
        query = query.where(Event.start_datetime >= filters.start_date)
    if filters.end_date:
        query = query.where(Event.start_datetime <= filters.end_date)

    if filters.is_online is not None:
        query = query.where(Event.is_online == filters.is_online)

    if filters.status:
        query = query.where(Event.status == filters.status)

    if filters.tag:
        query = query.where(Event.tags.ilike(f"%{filters.tag}%"))

    query = query.order_by(Event.start_datetime.asc())
    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())
