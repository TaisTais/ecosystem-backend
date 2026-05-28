from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user_by_token, get_current_moderator_or_admin
from src.database import get_session
from src.models.feed import PostType
from src.models.users import User
from src.schemas.feed import (
    PostCreate, PostRead, PostDetailRead, PostWithComments,
    PostFilter, PostUpdate, CommentCreate, CommentRead, PostCreateResponse
)
from src.services.feed import (
    create_post, get_posts_feed, get_post_detail,
    get_post_with_comments, update_post, delete_post, create_comment, toggle_like, toggle_post_publication,
    delete_comment, get_my_posts
)

router = APIRouter(prefix="/feed", tags=["Лента"])


@router.post("/", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED, summary="Добавить пост")
async def r_create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Создать новый пост (житель, организация или модератор)"""
    post = await create_post(session, data, current_user)

    # Вручную формируем ответ
    return PostCreateResponse(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author.name,
        author_role=post.author.role.value,
        post_type=post.post_type,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        tags=post.tags.split(',') if post.tags else None,
        event_id=post.event_id,
        created_at=post.created_at,
        is_published=post.is_published
    )


@router.get("/", response_model=List[PostRead], summary="Загрузить ленту постов")
async def r_get_posts_feed(
    post_type: Optional[PostType] = Query(None, description="Тип поста"),
    tag: Optional[str] = Query(None, description="Тег"),
    author_id: Optional[int] = Query(None, description="Автор"),
    skip: int = Query(0, ge=0, description="Сколько пропустить"),
    limit: int = Query(20, ge=1, le=50, description="Сколько вернуть"),
    session: AsyncSession = Depends(get_session)
):
    """Основная лента постов"""
    filters = PostFilter(
        post_type=post_type,
        tag=tag,
        author_id=author_id,
        skip=skip,
        limit=limit
    )
    return await get_posts_feed(session, filters)


@router.get("/my", response_model=List[PostRead], summary="Мои посты (включая черновики)")
async def r_get_my_posts(
    is_published: Optional[bool] = Query(None, description="None - все, true - опубликованные, false - скрытые"),
    post_type: Optional[PostType] = Query(None),
    tag: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Получить все свои посты"""
    filters = PostFilter(
        is_published=is_published,
        post_type=post_type,
        tag=tag,
        skip=skip,
        limit=limit
    )
    return await get_my_posts(session, current_user, filters)


@router.get("/{post_id}", response_model=PostDetailRead, summary="Развернуть пост")
async def r_get_post_detail(
    post_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить пост с полным текстом (развернуть в ленте)"""
    return await get_post_detail(session, post_id)


@router.get("/{post_id}/full", response_model=PostWithComments, summary="Посмотреть комментарии")
async def r_get_post_with_comments(
    post_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Полная страница поста + комментарии"""
    return await get_post_with_comments(session, post_id)


@router.patch("/{post_id}/edit", response_model=PostRead, summary="Редактировать пост")
async def r_update_post(
    post_id: int,
    data: PostUpdate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Редактировать содержание поста (только автор)"""
    return await update_post(session, post_id, data, current_user)


@router.patch("/{post_id}/publication", response_model=PostRead, summary="Опубликовать/скрыть пост")
async def r_toggle_post_publication(
    post_id: int,
    is_published: bool = Query(..., description="Опубликовать (true) или скрыть (false)"),
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Скрыть или опубликовать пост (автор или модератор)"""
    return await toggle_post_publication(session, post_id, is_published, current_user)


@router.delete("/{post_id}", status_code=status.HTTP_200_OK, summary="Удалить пост")
async def r_delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Удалить пост"""
    return await delete_post(session, post_id, current_user)


# ====================== ЛАЙКИ ======================
@router.post("/{post_id}/like", response_model=dict, summary="Поставить/убрать лайк")
async def toggle_post_like(
    post_id: int,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Поставить или убрать лайк под постом"""
    return await toggle_like(session, post_id, current_user)


# ====================== КОММЕНТАРИИ ======================
@router.post("/{post_id}/comments", response_model=CommentRead, summary="Добавить комментарий")
async def add_comment_to_post(
    post_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Добавить комментарий"""
    return await create_comment(session, post_id, data, current_user)


@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_200_OK, summary="Удалить комментарий")
async def r_delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_session)
):
    """Удалить комментарий (мягкое удаление)"""
    return await delete_comment(session, comment_id, current_user)
