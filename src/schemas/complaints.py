from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.models.complaints import TargetType, ComplaintStatus


class ComplaintBase(BaseModel):
    """Базовые поля жалобы"""
    target_type: TargetType
    target_id: int
    comment: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    """Создание жалобы (пользователем)"""
    # complainant_id определяется автоматически из current_user
    pass


class ComplaintRead(ComplaintBase):
    """Информация о жалобе (для пользователя и модератора)"""
    id: int
    complainant_id: int
    status: ComplaintStatus

    class Config:
        from_attributes = True


class ComplaintDetailRead(ComplaintRead):
    """Информация о жалобе (для пользователя и модератора)"""
    created_at: datetime
    moderated_at: Optional[datetime] = None
    moderator_id: Optional[int] = None
    moderator_response: Optional[str] = None

    class Config:
        from_attributes = True


class ComplaintUpdate(BaseModel):
    """Обновление жалобы модератором (принятие решения)"""
    status: ComplaintStatus
    moderator_response: Optional[str] = None


class ComplaintList(BaseModel):
    """Список жалоб (для модератора)"""
    complaints: List[ComplaintRead]
    total: int
