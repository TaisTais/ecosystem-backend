from sqlalchemy import Integer, DateTime, ForeignKey, Text, and_, literal_column
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign, remote
import enum
from sqlalchemy import Enum as SQLEnum
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from src.database import Base
from src.models.feed import Post

if TYPE_CHECKING:
    from src.models.events import Event
    from src.models.users import User
    from src.models.feed import Post


class TargetType(str, enum.Enum):
    CONTENT = "content"
    EVENT = "event"
    USER = "user"


class ComplaintStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress",
    APPROVED = "approved",
    REJECTED = "rejected"


class Complaint(Base):
    """Жалоба на контент, событие или пользователя"""
    __tablename__ = "complaint"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complainant_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    target_type: Mapped[TargetType] = mapped_column(SQLEnum(TargetType), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[ComplaintStatus] = mapped_column(SQLEnum(ComplaintStatus), default="pending", index=True)
    moderator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    moderator_response: Mapped[str] = mapped_column(Text)

    # Связи
    complainant: Mapped["User"] = relationship(
        "User",
        foreign_keys=[complainant_id],
        back_populates="complaints_made"
    )
    moderator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[moderator_id]
    )
    users: Mapped[Optional["User"]] = relationship(
        "User",
        primaryjoin="and_(User.id == foreign(Complaint.target_id), Complaint.target_type == 'user')",
        back_populates="complaints_received",
        uselist=False,
        viewonly=True,
    )

    posts: Mapped[Optional["Post"]] = relationship(
        "Post",
        primaryjoin="and_(Post.id == foreign(Complaint.target_id), Complaint.target_type == 'post')",
        back_populates="complaints",
        uselist=False,
        viewonly=True
    )

    events: Mapped[Optional["Event"]] = relationship(
        "Event",
        primaryjoin="and_(Event.id == foreign(Complaint.target_id), Complaint.target_type == 'event')",
        back_populates="complaints",
        uselist=False,
        viewonly=True,
    )
