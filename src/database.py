from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://pumba:tumba@localhost:5432/ecosystem_db"
async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,   # важно для асинхронности
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт новую сессию для каждого запроса"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy.
    Все таблицы будут наследоваться от него."""
    pass
