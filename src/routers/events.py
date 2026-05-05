from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_session
from src.schemas.events import EventRead, EventFilter
from src.services.events import get_events_calendar

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/calendar", response_model=List[EventRead])
async def get_calendar_events(
    filters: EventFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session)
):
    """Просмотр календаря событий с фильтрами"""
    return await get_events_calendar(
        session=session,
        filters=filters,
        skip=skip,
        limit=limit
    )
