from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional

from sqlalchemy.orm import selectinload

from src.models import User, Event
from src.models.feed import Post, PostComment, PostType, PostLike
from src.schemas.feed import PostFilter, PostRead, PostUpdate, PostDetailRead, PostCreate, CommentCreate, \
    PostWithComments, CommentRead
from src.services.utils import normalize_tags


async def create_post(session: AsyncSession, data: PostCreate, current_user: User) -> Post:
    """Создание нового поста в ленте"""

    # Если это приглашение на событие — проверяем права
    event_id = data.event_id

    if data.post_type == PostType.EVENT_INVITE:
        if not event_id or event_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для типа EVENT_INVITE обязательно нужно указать корректный event_id"
            )

        # Проверяем существование события
        event_result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = event_result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Событие с id={event_id} не найдено"
            )

        # Проверка прав
        is_organizer = any(org.id == current_user.id for org in event.organizers)
        if not is_organizer and current_user.role not in ["moderator", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не можете публиковать приглашение к этому событию"
            )
    else:
        # Для обычных постов event_id должен быть None
        event_id = None

    new_post = Post(
        author_id=current_user.id,
        post_type=data.post_type,
        title=data.title,
        content=data.content,
        image_url=data.image_url,
        tags=normalize_tags(data.tags),
        event_id=event_id,
        is_published=True
    )

    session.add(new_post)
    await session.commit()
    await session.refresh(new_post, ["author"])

    return new_post


async def get_posts_feed(
    session: AsyncSession,
    filters: PostFilter
) -> List[PostRead]:
    """Получить ленту постов"""

    query = select(Post).where(Post.is_published == True)

    if filters.post_type:
        query = query.where(Post.post_type == filters.post_type)

    if filters.tag:
        query = query.where(Post.tags.ilike(f"%{filters.tag}%"))

    if filters.author_id:
        query = query.where(Post.author_id == filters.author_id)

    query = query.options(selectinload(Post.author))
    query = query.order_by(desc(Post.created_at))
    query = query.offset(filters.skip).limit(filters.limit)

    result = await session.execute(query)
    posts = result.scalars().all()

    # Ручное формирование ответа
    response = []
    for post in posts:
        # Сокращаем текст для ленты
        content_preview = post.content
        if len(content_preview) > 250:
            content_preview = content_preview[:247] + "..."

        active_comments_count = len([
            c for c in post.comments if not getattr(c, 'is_deleted', False)
        ])

        response.append(PostRead(
            id=post.id,
            author_id=post.author_id,
            author_name=post.author.name if post.author else "Неизвестно",
            author_role=post.author.role.value if post.author else "unknown",
            post_type=post.post_type,
            title=post.title,
            content=content_preview,
            image_url=post.image_url,
            tags=[tag.strip() for tag in post.tags.split(',')] if post.tags else [],
            event_id=post.event_id,
            created_at=post.created_at,
            is_published=post.is_published,
            likes_count=len(post.likes),
            comments_count=active_comments_count
        ))

    return response


async def get_post_by_id(session: AsyncSession, post_id: int,) -> Post:
    """Внутренняя функция: получить SQLAlchemy объект поста"""
    query = select(Post).where(Post.id == post_id)

    result = await session.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    return post


async def get_post_detail(session: AsyncSession, post_id: int) -> PostDetailRead:
    """Получить полный пост (для детальной страницы)"""
    post = await get_post_by_id(session, post_id)

    if not post.author:
        await session.refresh(post, ["author"])

    return PostDetailRead(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author.name if post.author else "Неизвестно",
        author_role=post.author.role.value if post.author else "unknown",
        post_type=post.post_type,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        tags=[tag.strip() for tag in post.tags.split(',')] if post.tags else [],
        event_id=post.event_id,
        created_at=post.created_at,
        is_published=post.is_published,
        likes_count=len(post.likes),
        comments_count=len(post.comments)
    )


async def get_post_with_comments(session: AsyncSession, post_id: int) -> PostWithComments:
    """Получить пост + все комментарии (для детальной страницы)"""
    post = await get_post_by_id(session, post_id)

    # Загружаем автора
    if not post.author:
        await session.refresh(post, ["author"])

    # Загружаем комментарии
    comments_result = await session.execute(
        select(PostComment)
        .where(
            PostComment.post_id == post_id,
            PostComment.is_deleted == False
        )
        .order_by(desc(PostComment.created_at))
    )
    comments = comments_result.scalars().all()

    # Ручное формирование ответа
    return PostWithComments(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author.name if post.author else "Неизвестно",
        author_role=post.author.role.value if post.author else "unknown",
        post_type=post.post_type,
        title=post.title,
        content=post.content,                    # полный текст
        image_url=post.image_url,
        tags=[tag.strip() for tag in post.tags.split(',')] if post.tags else [],
        event_id=post.event_id,
        created_at=post.created_at,
        is_published=post.is_published,
        likes_count=len(post.likes),
        comments_count=len(post.comments),
        comments=[CommentRead.model_validate(c) for c in comments]
    )


async def get_my_posts(session: AsyncSession, current_user: User, filters: PostFilter) -> List[PostRead]:
    """Получить все посты текущего пользователя (включая скрытые)"""

    query = select(Post).where(Post.author_id == current_user.id)

    if filters.is_published is not None:
        query = query.where(Post.is_published == filters.is_published)

    if filters.post_type:
        query = query.where(Post.post_type == filters.post_type)

    if filters.tag:
        query = query.where(Post.tags.ilike(f"%{filters.tag}%"))

    query = query.options(selectinload(Post.author))
    query = query.order_by(desc(Post.created_at))
    query = query.offset(filters.skip).limit(filters.limit)

    result = await session.execute(query)
    posts = result.scalars().all()

    response = []
    for post in posts:
        content_preview = post.content
        if len(content_preview) > 250:
            content_preview = content_preview[:247] + "..."

        response.append(PostRead(
            id=post.id,
            author_id=post.author_id,
            author_name=post.author.name,
            author_role=post.author.role.value,
            post_type=post.post_type,
            title=post.title,
            content=content_preview,
            image_url=post.image_url,
            tags=[tag.strip() for tag in post.tags.split(',')] if post.tags else [],
            event_id=post.event_id,
            created_at=post.created_at,
            is_published=post.is_published,
            likes_count=len(post.likes),
            comments_count=len([c for c in post.comments if not getattr(c, 'is_deleted', False)])
        ))

    return response


async def update_post(session: AsyncSession, post_id: int, data: PostUpdate, current_user: User) -> PostRead:
    """Редактирование содержания поста — только автор"""
    post = await get_post_by_id(session, post_id)

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Редактировать содержание поста может только автор"
        )

    # Обновляем поля
    if data.title is not None:
        post.title = data.title
    if data.content is not None:
        post.content = data.content
    if data.image_url is not None:
        post.image_url = data.image_url
    if data.tags is not None:
        post.tags = normalize_tags(data.tags)
    if data.is_published is not None:
        post.is_published = data.is_published

    await session.commit()
    await session.refresh(post, ["author"])  # загружаем автора

    # Ручное формирование ответа
    return PostRead(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author.name if post.author else "Неизвестно",
        author_role=post.author.role.value if post.author else "unknown",
        post_type=post.post_type,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        tags=[tag.strip() for tag in post.tags.split(',')] if post.tags else [],
        event_id=post.event_id,
        created_at=post.created_at,
        is_published=post.is_published,
        likes_count=len(post.likes),
        comments_count=len(post.comments)
    )


async def toggle_post_publication(session: AsyncSession, post_id: int, is_published: bool, current_user: User) -> PostRead:
    """Скрытие или публикация поста (автор + модератор/админ)"""
    post = await get_post_by_id(session, post_id)

    if post.author_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для изменения статуса публикации"
        )

    post.is_published = is_published
    await session.commit()
    await session.refresh(post, ["author"])   # загружаем автора

    # Ручное формирование ответа
    return PostRead(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author.name if post.author else "Неизвестно",
        author_role=post.author.role.value if post.author else "unknown",
        post_type=post.post_type,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        tags=[tag.strip() for tag in post.tags.split(',')] if post.tags else [],
        event_id=post.event_id,
        created_at=post.created_at,
        is_published=post.is_published,
        likes_count=len(post.likes),
        comments_count=len(post.comments)
    )


async def delete_post(session: AsyncSession, post_id: int, current_user: User) -> dict:
    """Удаление поста (автор или модератор/админ)"""
    post = await get_post_by_id(session, post_id)

    # Проверка прав
    if post.author_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление поста"
        )

    await session.delete(post)
    await session.commit()

    return {"message": "Пост успешно удалён"}


async def toggle_like(session: AsyncSession, post_id: int, current_user: User) -> dict:
    """Поставить или убрать лайк под постом"""

    # Проверяем существование поста
    post = await get_post_by_id(session, post_id)

    # Проверяем, стоит ли уже лайк
    result = await session.execute(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.liker_id == current_user.id
        )
    )
    existing_like = result.scalar_one_or_none()
    if existing_like:
        # Убираем лайк
        await session.delete(existing_like)
        is_liked = False
    else:
        # Ставим лайк
        new_like = PostLike(
            post_id=post_id,
            liker_id=current_user.id
        )
        session.add(new_like)
        is_liked = True

    await session.commit()

    # Получаем актуальное количество лайков
    likes_count_result = await session.execute(
        select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    )
    likes_count = likes_count_result.scalar() or 0

    return {
        "post_id": post_id,
        "user_id": current_user.id,
        "is_liked": is_liked,
        "likes_count": likes_count
    }


async def create_comment(session: AsyncSession,  post_id: int,  data: CommentCreate,  current_user: User) -> CommentRead:
    """Добавление комментария под пост"""

    # Проверяем существование опубликованного поста
    result = await session.execute(
        select(Post).where(
            Post.id == post_id,
            Post.is_published == True
        )
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден или недоступен для комментирования"
        )

    new_comment = PostComment(
        post_id=post_id,
        commentator_id=current_user.id,
        content=data.content
    )

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment, ["commentator"])

    return CommentRead(
        id=new_comment.id,
        post_id=new_comment.post_id,
        commentator_id=new_comment.commentator_id,
        commentator_name=new_comment.commentator.name if new_comment.commentator else "Неизвестно",
        content=new_comment.content,
        created_at=new_comment.created_at
    )


async def delete_comment(session: AsyncSession, comment_id: int, current_user: User) -> dict:
    """Удаление комментария (автор/модератор/админ)"""

    result = await session.execute(
        select(PostComment).where(PostComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Проверка прав
    if comment.commentator_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Нет прав на удаление этого комментария"
        )

    comment.is_deleted = True
    comment.deleted_at = datetime.now(timezone.utc)
    comment.deleted_by = current_user.id
    await session.commit()
    return {
        "message": "Комментарий успешно удалён",
        "comment_id": comment_id
    }
