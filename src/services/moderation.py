from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.models.achievements import ActionType
from src.models.moderation import ModerationRecord, ModerationStatus
from src.models.users import User
from src.models.map import EcoPoint, Visit
from src.schemas.moderation import ModerationDecisionRead, ModerationDecisionCreate, ModerationRecordDetailRead
from src.services.achievements import award_achievement


async def apply_add_point(session: AsyncSession, mod: ModerationRecord) -> EcoPoint:
    """Применить создание новой эко-точки"""
    if not mod.new_data:
        raise HTTPException(status_code=400, detail="Нет данных для создания точки")

    new_point = EcoPoint(
        name=mod.new_data["name"],
        address=mod.new_data["address"],
        latitude=mod.new_data["latitude"],
        longitude=mod.new_data["longitude"],
        type=mod.new_data["type"],
        description=mod.new_data.get("description"),
        working_hours=mod.new_data.get("working_hours"),
        source="local",
        created_by_id=mod.user_id,
        created_at=datetime.now(timezone.utc),
        last_local_update_at=datetime.now(timezone.utc)
    )

    session.add(new_point)
    await session.commit()
    await session.refresh(new_point)

    # Привязываем id созданной точки к записи модерации
    mod.action_id = new_point.id
    return new_point


async def apply_update_point(session: AsyncSession, mod: ModerationRecord) -> EcoPoint:
    """Применить обновление существующей эко-точки"""
    if not mod.new_data or not mod.action_id:
        raise HTTPException(status_code=400, detail="Нет данных для обновления точки")

    result = await session.execute(
        select(EcoPoint).where(EcoPoint.id == mod.action_id)
    )
    point = result.scalar_one_or_none()

    if not point:
        raise HTTPException(status_code=404, detail="Эко-точка не найдена")

    # Применяем изменения
    for key, value in mod.new_data.items():
        if hasattr(point, key) and value is not None:
            setattr(point, key, value)

    point.last_local_update_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(point)
    return point


async def apply_visit_approval(session: AsyncSession, mod: ModerationRecord) -> Visit:
    """Подтвердить посещение эко-точки"""
    if not mod.action_id:
        raise HTTPException(status_code=400, detail="Нет id посещения")

    result = await session.execute(
        select(Visit).where(Visit.id == mod.action_id)
    )
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(status_code=404, detail="Посещение не найдено")

    await session.commit()
    await session.refresh(visit)
    return visit


async def approve_moderation(session: AsyncSession, moderation_id: int, moderator: User, decision: ModerationDecisionCreate) -> ModerationDecisionRead:
    """Модератор одобряет заявку"""

    mod = await get_moderation_by_id(session, moderation_id)

    if mod.status != ModerationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Заявка уже обработана")

    # ==================== ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ ====================
    if mod.action_type == ActionType.ADD_POINT:
        await apply_add_point(session, mod)
    elif mod.action_type == ActionType.UPDATE_POINT:
        await apply_update_point(session, mod)
    elif mod.action_type in (ActionType.VISIT_RECYCLING_POINT, ActionType.VISIT_OWN_TARA_POINT):
        await apply_visit_approval(session, mod)
    else:
        raise HTTPException(status_code=400, detail=f"Неизвестный тип действия: {mod.action_type}")

    # ==================== НАЧИСЛЕНИЕ ДОСТИЖЕНИЯ ====================
    try:
        await award_achievement(
            session=session,
            user_id=mod.user_id,
            action_type=mod.action_type
        )
    except Exception as e:
        print(f"[!] Ошибка начисления достижения: {e}")  # не прерываем одобрение

    # ==================== ОБНОВЛЕНИЕ МОДЕРАЦИИ ====================
    mod.status = ModerationStatus.APPROVED
    mod.moderator_id = moderator.id
    mod.moderated_at = datetime.now(timezone.utc)
    mod.moderator_comment = decision.moderator_comment   # ← теперь можно оставить комментарий

    await session.commit()
    await session.refresh(mod)

    return ModerationDecisionRead(
        success=True,
        message="Заявка одобрена",
        moderation_id=mod.id,
        action_type=mod.action_type.value,
        action_id=mod.action_id,
        status=mod.status.value,
        moderator_comment=mod.moderator_comment,
        moderated_at=mod.moderated_at
    )


async def reject_moderation(session: AsyncSession, moderation_id: int, moderator: User, decision: ModerationDecisionCreate) -> ModerationDecisionRead:
    """Модератор отклоняет заявку"""

    mod = await get_moderation_by_id(session, moderation_id)
    if mod.status != ModerationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Заявка уже обработана")

    mod.status = ModerationStatus.REJECTED
    mod.moderator_id = moderator.id
    mod.moderated_at = datetime.now(timezone.utc)
    mod.moderator_comment = decision.moderator_comment or "Отклонено модератором"

    await session.commit()
    await session.refresh(mod)

    return ModerationDecisionRead(
        success=True,
        message="Заявка отклонена",
        moderation_id=mod.id,
        action_type=mod.action_type.value,
        action_id=mod.action_id,
        status=mod.status.value,
        moderator_comment=mod.moderator_comment,
        moderated_at=mod.moderated_at
    )


async def get_moderations(
    session: AsyncSession,
    action_type: Optional[ActionType] = None,
    status: Optional[ModerationStatus] = None,
    moderator_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
) -> List[ModerationRecord]:
    """Получить список заявок на модерацию с фильтрами (для модератора)"""

    query = select(ModerationRecord).order_by(ModerationRecord.created_at.desc())

    if action_type:
        query = query.where(ModerationRecord.action_type == action_type)

    if status:
        query = query.where(ModerationRecord.status == status)

    if moderator_id:
        query = query.where(ModerationRecord.moderator_id == moderator_id)

    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_moderation_by_id(session: AsyncSession, moderation_id: int) -> ModerationRecord:
    result = await session.execute(
        select(ModerationRecord).where(ModerationRecord.id == moderation_id)
    )
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Запись модерации не найдена")
    return mod


async def get_moderations_by_user_id(
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
) -> List[ModerationRecord]:
    """Получить все заявки конкретного пользователя"""

    query = select(ModerationRecord).where(
        ModerationRecord.user_id == user_id
    ).order_by(ModerationRecord.created_at.desc())

    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())
