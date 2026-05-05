from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from src.models.feed import Post
from src.schemas.feed import PostFilter, PostRead
from src.services.utils import normalize_tags

async def get_feed(
        session: AsyncSession,
        filters: PostFilter,
        skip: int = 0,
        limit: int = 20
) -> List[Post]:
    """Получить ленту постов с фильтрами"""

    query = select(Post).where(Post.is_published)

    if filters.post_type:
        query = query.where(Post.post_type == filters.post_type)

    if filters.tag:
        query = query.where(Post.tags.ilike(f"%{filters.tag}%"))

    if filters.author_id:
        query = query.where(Post.author_id == filters.author_id)

    query = query.order_by(Post.created_at.desc()).offset(skip).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())
