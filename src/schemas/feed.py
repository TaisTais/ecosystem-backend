from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from src.models import User
from src.models.feed import PostType


class PostBase(BaseModel):
    """Базовые поля поста/статьи"""
    title: Optional[str] = None
    content: str
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    event_id: Optional[int] = None


class PostFilter(BaseModel):
    """Фильтры для ленты постов"""
    post_type: Optional[PostType] = None
    tag: Optional[str] = None
    author_id: Optional[int] = None
    skip: int = 0
    limit: int = 20
    is_published: Optional[bool] = None

    class Config:
        extra = "forbid"


class PostCreate(PostBase):
    """Создание поста"""
    post_type: PostType = PostType.POST
    is_published: bool = True

    @field_validator('event_id')
    @classmethod
    def validate_event_for_invite(cls, v, info):
        post_type = info.data.get('post_type')
        if post_type == PostType.EVENT_INVITE and not v:
            raise ValueError('Для типа EVENT_INVITE обязательно нужно указать event_id')
        return v


class PostCreateResponse(BaseModel):
    """Ответ после создания поста"""
    id: int
    author_id: int
    author_name: str
    author_role: str
    post_type: PostType
    title: Optional[str] = None
    content: str
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    event_id: Optional[int] = None
    created_at: datetime
    is_published: bool = True

    class Config:
        from_attributes = True


class PostRead(PostBase):
    """Пост для отображения в ленте"""
    id: int
    author_id: int
    author_name: str
    author_role: str
    post_type: PostType
    tags: Optional[List[str]] = None
    created_at: datetime
    is_published: bool = True
    is_deleted: bool = False
    likes_count: int = 0
    comments_count: int = 0

    class Config:
        from_attributes = True


class PostDetailRead(PostRead):
    """Полная версия поста (детальная страница)"""
    deleted_at: Optional[datetime] = None
    deleted_reason: Optional[str] = None


class PostUpdate(BaseModel):
    """Редактирование поста (автором или модератором)"""
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None


# ====================== КОММЕНТАРИИ ======================

class CommentCreate(BaseModel):
    """Создание комментария"""
    content: str


class CommentRead(BaseModel):
    """Отображение комментария"""
    id: int
    post_id: int
    commentator_id: int
    commentator_name: str
    content: str
    created_at: datetime
    is_deleted: bool = False
    deleted_at: datetime
    deleted_reason: Optional[str] = None

    class Config:
        from_attributes = True


class PostWithComments(PostRead):
    """Пост + все комментарии (для детальной страницы)"""
    comments: List[CommentRead] = []


# ====================== ЛАЙКИ ======================

class PostLikeCreate(BaseModel):
    """Техническая схема (лайк ставится по POST /feed/{post_id}/like)"""
    pass  # пользователь просто нажимает "лайк"


class PostLikeRead(BaseModel):
    """Информация о лайке"""
    post_id: int
    liker_id: int
    created_at: datetime
    likes_count: int

    class Config:
        from_attributes = True
