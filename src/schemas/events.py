from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from src.models.events import EventStatus


class EventBase(BaseModel):
    """Базовая информация о мероприятии"""
    title: str
    description: str
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    status: EventStatus = EventStatus.ACTIVE
    is_online: bool = False
    address: Optional[str] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    tags: Optional[List[str]] = None


class EventCreate(EventBase):
    """Создание нового мероприятия"""

    @field_validator('meeting_link')
    @classmethod
    def validate_online_event(cls, v, info):
        is_online = info.data.get('is_online')
        if is_online and not v:
            raise ValueError('Для онлайн-мероприятия обязательна ссылка на встречу')
        if not is_online and v:
            raise ValueError('Для оффлайн-мероприятия не нужно указывать meeting_link')
        return v

    @field_validator('address')
    @classmethod
    def validate_offline_event(cls, v, info):
        is_online = info.data.get('is_online')
        if not is_online and not v:
            raise ValueError('Для оффлайн-мероприятия обязателен адрес')
        return v


class EventRead(EventBase):
    """Мероприятие для отображения в календаре и ленте"""
    id: int
    organizer_id: int
    organizer_name: str
    organizer_role: str
    applicants_count: int = 0
    participants_count: int = 0
    created_at: datetime
    is_user_applicant: bool = False
    has_user_confirmed: bool = False

    class Config:
        from_attributes = True


class EventUpdate(BaseModel):
    """Редактирование мероприятия (организатором или модератором)"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_online: Optional[bool] = None
    address: Optional[str] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    tags: Optional[List[str]] = None
    status: Optional[EventStatus] = None


class EventDetail(EventRead):
    """Полная карточка мероприятия"""
    applicants: List["EventApplicantRead"] = []
    participants: List["EventParticipantRead"] = []


# ====================== ЗАПИСЬ НА МЕРОПРИЯТИЕ ======================

class EventApplicantCreate(BaseModel):
    """Пользователь записывается на мероприятие (становится applicant)"""
    pass


class EventApplicantRead(BaseModel):
    """Информация о записавшемся"""
    user_id: int
    user_name: str
    registered_at: datetime

    class Config:
        from_attributes = True


# ====================== ПОДТВЕРЖДЕНИЕ УЧАСТИЯ ======================

class EventParticipantCreate(BaseModel):
    """Пользователь регистрирует посещение (становится participant)"""
    proof_photo_url: str
    comment: Optional[str] = None


class EventParticipantRead(BaseModel):
    """Информация о участнике"""
    user_id: int
    user_name: str
    confirmed_at: datetime
    proof_photo_url: str

    class Config:
        from_attributes = True
