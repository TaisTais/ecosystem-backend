from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from src.models.feed import PostType


class PostBase(BaseModel):
    """Базовые поля поста/статьи"""
    title: Optional[str] = None
    content: str
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None


class PostFilter(BaseModel):
    """Фильтры для ленты постов"""
    post_type: Optional[PostType] = None
    tag: Optional[str] = None
    author_id: Optional[int] = None


class PostCreate(PostBase):
    """Создание поста (пользователем, организацией или модератором)"""
    post_type: PostType = PostType.POST

    @field_validator('post_type')
    @classmethod
    def validate_post_type(cls, v: PostType) -> PostType:
        # Можно добавить дополнительные ограничения по ролям позже
        return v


class PostRead(PostBase):
    """Пост для отображения в ленте"""
    id: int
    author_id: int
    author_name: str
    author_role: str
    post_type: PostType
    created_at: datetime
    is_published: bool = True
    likes_count: int = 0
    comments_count: int = 0

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class PostWithComments(PostRead):
    """Пост + все комментарии (для детальной страницы)"""
    comments: List[CommentRead] = []


# ====================== ЛАЙКИ ======================

class PostLikeCreate(BaseModel):
    """Техническая схема (обычно не используется напрямую)"""
    pass  # пользователь просто нажимает "лайк"


class PostLikeRead(BaseModel):
    """Информация о лайке (если нужно)"""
    post_id: int
    liker_id: int
    created_at: datetime

    class Config:
        from_attributes = True
