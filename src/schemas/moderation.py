from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.models.moderation import ActionType, ModerationStatus


class ModerationRecordRead(BaseModel):
    """Для обычного пользователя (его заявки)"""
    id: int
    action_type: ActionType
    action_id: int
    status: ModerationStatus
    created_at: datetime
    moderated_at: Optional[datetime] = None
    moderator_comment: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class ModerationRecordDetailRead(BaseModel):
    """Полная информация для модератора"""
    id: int
    action_type: ActionType
    action_id: int
    user_id: int
    user_name: Optional[str] = None
    old_data: Optional[dict] = None
    new_data: Optional[dict] = None
    status: ModerationStatus
    created_at: datetime
    moderator_id: Optional[int] = None
    moderator_name: Optional[str] = None
    moderator_comment: Optional[str] = None
    moderated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModerationDecisionCreate(BaseModel):
    """Что модератор отправляет при проверке заявки"""
    moderator_comment: Optional[str] = None


class ModerationDecisionRead(BaseModel):
    """Ответ после одобрения или отклонения заявки"""
    success: bool = True
    message: str
    moderation_id: int
    action_type: str
    action_id: int
    status: str
    moderator_comment: Optional[str] = None
    moderated_at: datetime

    class Config:
        from_attributes = True
