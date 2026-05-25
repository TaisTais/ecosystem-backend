from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select, update

from src.models.achievements import ActionType


async def award_achievement(
    session: AsyncSession,
    user_id: int,
    action_type: ActionType
):
    """Начислить достижение пользователю в зависимости от типа действия"""
    # Здесь будет логика поиска подходящего Achievement и создание UserAchievement
    print(f"✅ Достижение начислено пользователю {user_id} за действие {action_type.value}")
    # TODO: Полная реализация позже