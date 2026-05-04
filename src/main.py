from __future__ import annotations
from contextlib import asynccontextmanager

from src.database import async_engine, Base, async_session_maker
from src.seed import create_default_achievements
import uvicorn
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запускается при старте и завершении приложения"""
    print("🚀 Запуск приложения Экосистема...")

    # Создаём таблицы
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаём начальные данные
    async with async_session_maker() as session:
        await create_default_achievements(session)

    yield  # здесь приложение работает

    print("👋 Завершение приложения...")
    await async_engine.dispose()


app = FastAPI(
    title="Экосистема — API",
    description="Бэкенд для дипломного проекта 'Экосистема'",
    version="1.0.0",
    lifespan=lifespan
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)