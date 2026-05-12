from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from sqlalchemy import Enum as SQLEnum
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

from src.database import Base
if TYPE_CHECKING:
    from src.models.complaints import Complaint


class PostType(str, enum.Enum):
    POST = "post"
    ARTICLE = "article"
    CHALLENGE = "challenge"
    EVENT_INVITE = "event_invite"


class Post(Base):
    """Класс для любых видов постов в ленте (в том числе приглашения на мероприятие)"""
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    post_type: Mapped[PostType] = mapped_column(SQLEnum(PostType), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts",
        lazy="selectin"
    )
    comments: Mapped[List["PostComment"]] = relationship(
        "PostComment",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    likes: Mapped[List["PostLike"]] = relationship(
        "PostLike",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.target_id]",
        primaryjoin="and_(Complaint.target_id == Post.id, Complaint.target_type == 'post')",
        back_populates="posts",
        lazy="selectin"
    )

    @property
    def likes_count(self) -> int:
        return len(self.likes)

    @property
    def comments_count(self) -> int:
        return len(self.comments)


class PostComment(Base):
    """Комментарии под постами"""
    __tablename__ = "comment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=False)
    commentator_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments"
    )
    commentator: Mapped["User"] = relationship(
        "User"
    )


class PostLike(Base):
    """Лайки под постами"""
    __tablename__ = "post_like"
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), primary_key=True)
    liker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="likes"
    )
    liker: Mapped["User"] = relationship(
        "User"
    )
    __table_args__ = (
        UniqueConstraint('post_id', 'liker_id', name='uq_post_like'),
    )
