from __future__ import annotations
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, Depends, status
import uvicorn
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ==================== НАСТРОЙКИ ====================
DATABASE_URL = "postgresql+asyncpg://pumba:tumba@localhost:5432/ecosystem_db"

# Создаём асинхронный движок
async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ==================== БАЗОВЫЙ КЛАСС ====================
class Base(DeclarativeBase):
    pass


# ==================== МОДЕЛИ ТАБЛИЦ ====================
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience_points: Mapped[int] = mapped_column(Integer, default=0)


class Organisation(Base):
    __tablename__ = "organisation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class EcoPoint(Base):
    __tablename__ = "ecopoint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # === Идентификация источника ===
    recyclemap_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(20), default="local")   # "local" или "recyclemap"

    # === Основные данные ===
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    working_hours: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # === Пользовательские данные (защищены от перезаписи) ===
    local_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Примеры: "работает", "закрыто", "временно_не_работает", "не_принимает_пластик"

    status_confirmed_by: Mapped[int] = mapped_column(Integer, default=0)
    needs_review: Mapped[bool] = mapped_column(default=False)          # флаг, что нужно проверить статус

    # Даты
    recyclemap_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_local_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Кто создал точку (для локальных точек)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)

    # Связи
    created_by: Mapped[Optional["User"]] = relationship("User", back_populates="created_points")
    reviews: Mapped[List["EcoPointReview"]] = relationship("EcoPointReview", back_populates="ecopoint", cascade="all, delete-orphan")


class EcoPointReview(Base):
    __tablename__ = "ecopoint_review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ecopoint_id: Mapped[int] = mapped_column(ForeignKey("ecopoint.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(50))                    # статус, который подтвердил пользователь
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    ecopoint: Mapped["EcoPoint"] = relationship("EcoPoint", back_populates="reviews")
    user: Mapped["User"] = relationship("User")


# ==================== Pydantic СХЕМЫ ====================
class CreateUser(BaseModel):
    name: str
    email: Optional[str] = None
    level: int = 1


class CreateOrganisation(BaseModel):
    name: str
    description: Optional[str] = None


class CreateEvent(BaseModel):
    name: str
    description: Optional[str] = None
    date: Optional[str] = None


class CreateEcoPoint(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    category: str
    description: Optional[str] = None


# ==================== ЗАВИСИМОСТЬ ДЛЯ СЕССИИ ====================
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# ==================== LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔄 Создание таблиц в базе данных...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Все таблицы успешно созданы!")
    yield
    await async_engine.dispose()
    print("🛑 Соединение с базой закрыто.")


# ==================== FASTAPI ПРИЛОЖЕНИЕ ====================
app = FastAPI(
    title="Экосистема — API",
    description="Бэкенд для дипломного проекта 'Экосистема'",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== ЭНДПОИНТЫ ====================

@app.get("/", status_code=status.HTTP_200_OK, tags=["Главные ручки"])
async def root():
    return {"message": "API Экосистемы работает! Перейдите на /docs для документации"}


@app.post("/users", status_code=status.HTTP_201_CREATED, tags=["Главные ручки"])
async def create_user(user_data: CreateUser, session: AsyncSession = Depends(get_session)):
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        level=user_data.level
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@app.get("/users", status_code=status.HTTP_200_OK, tags=["Главные ручки"])
async def get_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    return result.scalars().all()


@app.post("/organisations", status_code=status.HTTP_201_CREATED, tags=["Главные ручки"])
async def create_organisation(org_data: CreateOrganisation, session: AsyncSession = Depends(get_session)):
    new_org = Organisation(name=org_data.name, description=org_data.description)
    session.add(new_org)
    await session.commit()
    await session.refresh(new_org)
    return new_org


@app.get("/events", status_code=status.HTTP_200_OK, tags=["Главные ручки"])
async def get_events(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Event))
    return result.scalars().all()

# @app.get("/events/{event_id}")
# def get_event(session: AsyncSession = Depends(), event_id: int):
#     for

@app.post("/ecopoints", status_code=status.HTTP_201_CREATED, tags=["Главные ручки"])
async def create_ecopoint(point: CreateEcoPoint, session: AsyncSession = Depends(get_session)):
    new_point = EcoPoint(
        name=point.name,
        address=point.address,
        latitude=point.latitude,
        longitude=point.longitude,
        category=point.category,
        description=point.description
    )
    session.add(new_point)
    await session.commit()
    await session.refresh(new_point)
    return new_point


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)