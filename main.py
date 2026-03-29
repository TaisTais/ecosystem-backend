from __future__ import annotations
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy import Column, Integer, String, select, Text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped
from pydantic import BaseModel
from fastapi import FastAPI, Depends

DATABASE_URL = "postgresql+asyncpg://pumba:tumba@localhost:5432/ecosystem_db"

async_engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=True,
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    future=True,
    autoflush=False,
    autocommit=False,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаём таблицы при запуске приложения"""
    print("🔄 Создаю таблицы...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Создаст ВСЕ таблицы из моделей
    print("✅ Таблицы созданы!")
    yield
    await async_engine.dispose()


async def get_session():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


class Base(DeclarativeBase):
    __abstract__ = True


class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50))
    level: Mapped[int] = Column(Integer, default=60)


class CreateUser(BaseModel):
    name: str
    level: int


app = FastAPI(lifespan=lifespan)


class Organisation(Base):
    __tablename__ = 'organisation'
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50))


class CreateOrganisation(BaseModel):
    name: str


class Event(Base):
    __tablename__ = 'event'
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50))




@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


@app.post("/users")
async def create_user(user_data: CreateUser, session: AsyncSession = Depends(get_session)):
    new_user = User(name=user_data.name, level=user_data.level)
    session.add(new_user)

    await session.commit()
    await session.refresh(new_user)
    return new_user


@app.get("/organisations")
async def get_organisations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Organisation))
    organisations = result.scalars().all()
    return organisations


@app.post("/organisations")
async def create_organisation(organisation_data: CreateOrganisation, session: AsyncSession = Depends(get_session)):
    new_organisation = Organisation(name=organisation_data.name)
    session.add(new_organisation)

    await session.commit()
    await session.refresh(new_organisation)
    return new_organisation

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)