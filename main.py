from __future__ import annotations
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List

import uvicorn
from fastapi import FastAPI, Depends, status, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, Boolean, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum
from sqlalchemy import Enum as SQLEnum

DATABASE_URL = "postgresql+asyncpg://pumba:tumba@localhost:5432/ecosystem_db"

async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,   # важно для асинхронности
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy.
    Все таблицы будут наследоваться от него."""
    pass


# <editor-fold desc="Пользователи">

class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    ORGANIZATION = "organization"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    """Универсальный класс для всех видов пользователей"""
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.CITIZEN, index=True)

    # Общие поля
    is_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    block_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Поля для обычных пользователей
    experience_points: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Поля для организаций
    description: Mapped[Optional[str]] = mapped_column(Text)
    inn: Mapped[Optional[str]] = mapped_column(String(20))

    # Связи
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author",
        lazy="selectin"
    )
    statuses: Mapped[List["Status"]] = relationship(
        "Status",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    created_points: Mapped[List["EcoPoint"]] = relationship(
        "EcoPoint",
        back_populates="created_by",
        lazy="selectin"
    )
    organized_events: Mapped[List["Event"]] = relationship(
        "Event",
        secondary="event_organizer",
        back_populates="organizers",
        lazy="selectin"
    )
    participated_events: Mapped[List["Event"]] = relationship(
        "Event",
        secondary="event_participant",
        back_populates="participants",
        lazy="selectin"
    )
    visits: Mapped[List["Visit"]] = relationship(
        "Visit",
        back_populates="visiters",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    achievements: Mapped[List["Achievement"]] = relationship(
        "Achievement",
        secondary="user_achievement",
        back_populates="users",
        lazy="selectin"
    )
    complaints_made: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.complainant_id]",
        back_populates="complainant",
        lazy="selectin"
    )
    complaints_received: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.target_id]",
        primaryjoin="and_(Complaint.target_id == User.id, Complaint.target_type == 'user')",
        back_populates="users",
        lazy="selectin"
    )

# </editor-fold>


# <editor-fold desc="Карта">
class SourceType(str, enum.Enum):
    LOCAL = "local"
    RECYCLEMAP = "recyclemap"


class PointStatus(str, enum.Enum):
    WORKING = "working"
    CLOSED = "closed"
    TEMPORARILY_CLOSED = "temporarily_closed"


class EcoPointCategory(str, enum.Enum):
    PLASTIC = "plastic"
    GLASS = "glass"
    PAPER = "paper"
    METAL = "metal"
    BATTERIES = "batteries"
    ELECTRONICS = "electronics"
    CLOTHES = "clothes"
    HAZARDOUS = "hazardous"
    OTHER = "other"


class EcoPoint(Base):
    """Эко-точка на интерактивной карте"""
    __tablename__ = "ecopoint"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recyclemap_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    source: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), nullable=False, default=SourceType.LOCAL, index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[EcoPointCategory] = mapped_column(SQLEnum(EcoPointCategory), nullable=False, index=True)
    working_hours: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    needs_review: Mapped[bool] = mapped_column(default=False)
    recyclemap_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_local_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Связи
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_points"
    )
    statuses: Mapped[List["Status"]] = relationship(
        "Status",
        back_populates="point",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="point",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    visits: Mapped[List["Visit"]] = relationship(
        "Visit",
        back_populates="point",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Status(Base):
    """Класс для статусов пользователей к эко-точкам на интерактивной карте"""
    __tablename__ = "ecopoint_status"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[PointStatus] = mapped_column(SQLEnum(PointStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    point: Mapped["EcoPoint"] = relationship(
        "EcoPoint",
        back_populates="statuses"
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="statuses"
    )


class Review(Base):
    """Класс для отзывов пользователей к эко-точкам на интерактивной карте"""
    __tablename__ = "ecopoint_review"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    point: Mapped["EcoPoint"] = relationship(
        "EcoPoint",
        back_populates="reviews"
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="reviews"
    )


class Visit(Base):
    """Класс для посещений пользователей эко-точек на интерактивной карте"""
    __tablename__ = "ecopoint_visit"
    visiter_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), primary_key=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    # Связи
    visiters: Mapped["User"] = relationship(
        "User",
        back_populates="visits"
    )
    point: Mapped["EcoPoint"] = relationship(
        "EcoPoint",
        back_populates="visits"
    )

# </editor-fold>


# <editor-fold desc="Мероприятия">
class Event(Base):
    """Класс для мероприятий в ленте постов и календаре"""
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255))
    date: Mapped[str] = mapped_column(String(50), nullable=False)
    time: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)

    # Связи
    organizers: Mapped[List["User"]] = relationship(
        "User",
        secondary="event_organizer",
        back_populates="organized_events",
        lazy="selectin"
    )
    participants: Mapped[List["User"]] = relationship(
        "User",
        secondary="event_participant",
        back_populates="participated_events",
        lazy="selectin"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.target_id]",
        primaryjoin="and_(Complaint.target_id == Event.id, Complaint.target_type == 'event')",
        back_populates="events",
        lazy="selectin"
    )


# ==================== ПРОМЕЖУТОЧНЫЕ ТАБЛИЦЫ ====================
class EventOrganizer(Base):
    """Промежуточная таблица: User(организаторы) - Event(мероприятия)"""
    __tablename__ = "event_organizer"
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))


class EventParticipant(Base):
    """Промежуточная таблица: User(участники) - Event(мероприятия)"""
    __tablename__ = "event_participant"
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

# </editor-fold>


# <editor-fold desc="Лента">
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
    tags: Mapped[Optional[str]] = mapped_column(String(150))  # "переработка", "субботник"...

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts",
        lazy="selectin"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.target_id]",
        primaryjoin="and_(Complaint.target_id == Post.id, Complaint.target_type == 'post')",
        back_populates="posts",
        lazy="selectin"
    )

# </editor-fold>


# <editor-fold desc="Жалобы">
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
    users: Mapped[Optional["Post"]] = relationship(
        "User",
        primaryjoin="and_(Complaint.target_id == User.id, Complaint.target_type == 'user')",
        back_populates="complaints_received",
        uselist=False
    )
    posts: Mapped[Optional["Post"]] = relationship(
        "Post",
        primaryjoin="and_(Complaint.target_id == Post.id, Complaint.target_type == 'post')",
        back_populates="complaints",
        uselist=False
    )
    events: Mapped[Optional["Event"]] = relationship(
        "Event",
        primaryjoin="and_(Complaint.target_id == Event.id, Complaint.target_type == 'event')",
        back_populates="complaints",
        uselist=False
    )
# </editor-fold>


# <editor-fold desc="Достижения и награды">
class ActionType(str, enum.Enum):
    ADD_POINT = "add_point"
    SET_STATUS = "set_status"
    WRITE_REVIEW = "write_review"
    PARTICIPATE_EVENT = "participate_event"
    ORGANIZE_EVENT = "organize_event"
    VISIT_RECYCLING_POINT = "visit_recycling_point"
    VISIT_OWN_TARA_POINT = "visit_own_tara_point"


class Achievement(Base):
    """Класс шаблон достижения"""
    __tablename__ = "achievement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(200))
    points_reward: Mapped[int] = mapped_column(Integer, default=0)

    # Награда
    badge_icon: Mapped[Optional[str]] = mapped_column(String(200))  # название файла иконки награды
    is_cumulative: Mapped[bool] = mapped_column(default=False)  # накопительное ли

    # Условия получения
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "add_point", "set_status"...
    required_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==================== ПРОМЕЖУТОЧНЫЕ ТАБЛИЦЫ ====================
class UserAchievement(Base):
    """Промежуточная таблица: User(участники) - Achievement(достижения)"""
    __tablename__ = "user_achievement"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievement.id"), primary_key=True)
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_moderated: Mapped[bool] = mapped_column(default=True)

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="achievements"
    )
    achievement: Mapped["Achievement"] = relationship(
        "Achievement"
    )


async def create_default_achievements(session: AsyncSession):
    """Создаёт базовый набор достижений при первом запуске"""

    result = await session.execute(select(Achievement).limit(1))
    if result.scalar_one_or_none():
        print("✅ Достижения уже существуют в базе")
        return

    achievements = [
        # === ЕДИНИЧНЫЕ ДОСТИЖЕНИЯ ===
        Achievement(
            name="Статус добавлен!",
            description="Спасибо, что поддерживаете актуальность карты",
            icon="first_status.png",
            points_reward=5,
            action_type=ActionType.SET_STATUS,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name="Отзыв опубликован!",
            description="Благодарим за обратную связь, вместе делаем карту лучше",
            icon="first_review.png",
            points_reward=10,
            action_type=ActionType.WRITE_REVIEW,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='На шаг ближе к zero waste!',
            description="Поход со своей тарой зарегистрирован, спасибо, что способствуете сокращению отходов!",
            icon="first_review.png",
            points_reward=15,
            action_type=ActionType.VISIT_OWN_TARA_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Разделяй и утилизируй!',
            description="Сдача вторсырья зарегистрирована, благодарим за осознанную утилизацию!",
            icon="first_review.png",
            points_reward=20,
            action_type=ActionType.VISIT_RECYCLING_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name="Ваша точка добавлена!",
            description="Благодаря вам карта города стала ещё шире и доступнее",
            icon="first_point.png",
            points_reward=30,
            action_type=ActionType.ADD_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Вместе мы сила!',
            description="Участие в мероприятии подтверждено, спасибо за ваш вклад!",
            icon="first_review.png",
            points_reward=30,
            action_type=ActionType.PARTICIPATE_EVENT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Объединяя город!',
            description="Вы успешно провели мероприятие, благодаря вашему труду город стал лучше!",
            icon="first_review.png",
            points_reward=50,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=1,
            is_cumulative=False
        ),

        # === ПЕРВЫЕ ДОСТИЖЕНИЯ ===
        Achievement(
            name="Первый отклик!",
            description="Спасибо за ваш первый вклад в поддержку актуальности карты",
            icon="first_status.png",
            points_reward=10,
            action_type=ActionType.SET_STATUS or ActionType.WRITE_REVIEW,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Первое приключение!',
            description="Поздравляем, вы посетили свою первую эко-точку, поделитесь впечатлениями?",
            icon="first_review.png",
            points_reward=20,
            action_type=ActionType.VISIT_OWN_TARA_POINT or ActionType.VISIT_RECYCLING_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name="Первый след!",
            description="Вы добавили свою первую эко-точку на карту",
            icon="first_point.png",
            points_reward=30,
            action_type=ActionType.ADD_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Начало дружбы!',
            description="Поздравляем, это было ваше первое мероприятие вместе с Экосистемой!",
            icon="first_review.png",
            points_reward=30,
            action_type=ActionType.PARTICIPATE_EVENT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='У этого города новый герой!',
            description="Вы организовали свое первое мероприятие и объединили силы горожан для общего блага!",
            icon="first_review.png",
            points_reward=50,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=1,
            is_cumulative=False
        ),

        # === НАКОПИТЕЛЬНЫЕ ДОСТИЖЕНИЯ ===

        Achievement(
            name="Человек высокого статуса!",
            description="Вы поставили 5 статусов, спасибо за активность!",
            badge_icon="badge_voice.png",
            points_reward=50,
            action_type=ActionType.SET_STATUS,
            required_count=20,
            is_cumulative=True
        ),
        Achievement(
            name="Кто отзывается, тот... для всех старается!",
            description="Вы оставили 5 отзывов на карте, спасибо за труд, коллега!",
            badge_icon="badge_review.png",
            points_reward=100,
            action_type=ActionType.WRITE_REVIEW,
            required_count=8,
            is_cumulative=True
        ),
        Achievement(
            name="Мы с Тамарой ходим с тарой!",
            description="Вы 5 раз посетили точки категории 'своя тара', так держать!",
            badge_icon="badge_zerowaste.png",
            points_reward=150,
            action_type=ActionType.VISIT_OWN_TARA_POINT,
            required_count=8,
            is_cumulative=True
        ),
        Achievement(
            name="Сдаёт сырьё, а не позиции!",
            description="Вы 5 раз посетили точки категории 'сдача сырья', сортировка – тяжелый труд, спасибо вам!",
            badge_icon="badge_cleaner.png",
            points_reward=200,
            action_type=ActionType.VISIT_RECYCLING_POINT,
            required_count=10,
            is_cumulative=True
        ),
        Achievement(
            name="Первопроходец Экосистемы!",
            description="Вы добавили 3 эко-точки на карту, благодарим настоящего знатока своего города!",
            badge_icon="badge_explorer.png",
            points_reward=150,
            action_type=ActionType.ADD_POINT,
            required_count=5,
            is_cumulative=True
        ),
        Achievement(
            name="Часть команды – часть Экосистемы!",
            description="Вы поучаствовали в 5 мероприятиях, город благодарен своему активному жителю!",
            badge_icon="badge_organizer.png",
            points_reward=200,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=2,
            is_cumulative=True
        ),
        Achievement(
            name="Прирождённый эко-лидер!",
            description="Вы организовали 3 мероприятия, Экосистема никогда не забудет ваш подвиг!",
            badge_icon="badge_organizer.png",
            points_reward=300,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=2,
            is_cumulative=True
        ),
    ]

    for ach in achievements:
        session.add(ach)

    await session.commit()
    print(f"✅ Создано {len(achievements)} достижений")
# </editor-fold>


# ==================== 6. PYDANTIC СХЕМЫ (ВАЛИДАЦИЯ API) ====================
class CreateUser(BaseModel):
    name: str
    email: Optional[str] = None
    level: int = 1


    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_roles = {"user"}
        if v not in allowed_roles:
            raise ValueError(f"Недопустимая роль. Разрешено только: {allowed_roles}")
        return v


class CreateOrganisation(BaseModel):
    name: str
    description: Optional[str] = None

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_roles = {"organization"}
        if v not in allowed_roles:
            raise ValueError(f"Недопустимая роль. Разрешено только: {allowed_roles}")
        return v


class CreateModerator(BaseModel):
    name: str
    email: str


class CreateEcoPoint(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    category: str
    description: Optional[str] = None


class CreateComplaint(BaseModel):
    target_type: str
    target_id: int
    reason: str
    comment: Optional[str] = None


# ==================== 7. ЗАВИСИМОСТЬ ДЛЯ СЕССИИ ====================
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт новую сессию для каждого запроса"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# ==================== 8. LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется при старте и остановке приложения"""
    print("🔄 Создание таблиц в базе данных...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        await create_default_achievements(session)
    print("✅ Все таблицы успешно созданы!")
    yield
    await async_engine.dispose()
    print("🛑 Соединение с базой закрыто.")


# ==================== 9. FASTAPI ПРИЛОЖЕНИЕ ====================
app = FastAPI(
    title="Экосистема — API",
    description="Бэкенд для дипломного проекта 'Экосистема'",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== 10. ЭНДПОИНТЫ ====================

@app.get("/")
async def root():
    return {"message": "API Экосистемы работает! Перейдите на /docs"}


@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: CreateUser, session: AsyncSession = Depends(get_session)):
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        level=user_data.level,
        role="user"
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@app.post("/organisations", status_code=status.HTTP_201_CREATED)
async def create_organisation(org_data: CreateOrganisation, session: AsyncSession = Depends(get_session)):
    new_org = Organisation(
        name=org_data.name,
        description=org_data.description,
        role="organization"
    )
    session.add(new_org)
    await session.commit()
    await session.refresh(new_org)
    return new_org


@app.post("/admin/create-moderator", status_code=status.HTTP_201_CREATED)
async def create_moderator(
    moderator_data: CreateModerator,
    session: AsyncSession = Depends(get_session)
):
    """Создание модератора (пока без защиты — позже добавим)"""
    new_moderator = Moderator(
        name=moderator_data.name,
        email=moderator_data.email,
        role="moderator"
    )
    session.add(new_moderator)
    await session.commit()
    await session.refresh(new_moderator)
    return {"message": "Модератор успешно создан", "id": new_moderator.id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)