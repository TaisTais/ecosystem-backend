from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_session
from src.schemas.feed import PostRead, PostFilter
from src.services.feed import get_feed

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get("/", response_model=List[PostRead])
async def get_posts_feed(
    filters: PostFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Просмотр ленты постов"""
    return await get_feed(
        session=session,
        filters=filters,
        skip=skip,
        limit=limit
    )
