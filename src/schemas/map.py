from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from src.models.achievements import ActionType
from src.models.map import SourceType, EcoPointStatus, EcoPointCategory


class EcoPointBase(BaseModel):
    """Общие поля для всех вариантов"""
    name: str
    address: str
    latitude: float
    longitude: float
    type: EcoPointCategory


# region СТАТУСЫ И ОТЗЫВЫ
class EcoPointStatusCreate(BaseModel):
    """Поставить статус точке (житель)"""
    status: EcoPointStatus

    class Config:
        from_attributes = True


class EcoPointStatusRead(BaseModel):
    """Один конкретный статус + статистика"""
    status: EcoPointStatus
    confirmed_by: int = 0
    last_updated_at: Optional[datetime] = None


class EcoPointMostConfirmedStatusRead(BaseModel):
    """Только самый подтвержденный статус для использования в списке"""
    most_confirmed_status: Optional[EcoPointStatusRead] = None


class EcoPointReviewCreate(BaseModel):
    """Оставить отзыв (житель)"""
    comment: str
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class EcoPointReviewRead(BaseModel):
    """Посмотреть отзывы к эко-точке"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    comment: str
    photo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# endregion


class EcoPointCreate(EcoPointBase):
    """Создать эко-точку (житель)"""
    description: Optional[str] = None
    working_hours: Optional[str] = None

    class Config:
        from_attributes = True


class EcoPointFilter(BaseModel):
    """Просмотр эко-точек с фильтрами"""
    type: Optional[EcoPointCategory] = None
    min_latitude: Optional[float] = None
    max_latitude: Optional[float] = None
    min_longitude: Optional[float] = None
    max_longitude: Optional[float] = None


class EcoPointListRead(EcoPointBase):
    """Сокращённая информация об эко-точках (для списка)"""
    id: int
    source: SourceType
    most_confirmed_status: EcoPointMostConfirmedStatusRead
    needs_review: bool = False

    class Config:
        from_attributes = True


class EcoPointRead(EcoPointBase):
    """Полная информация об эко-точке (для отдельной карточки)"""
    id: int
    recyclemap_id: Optional[str] = None
    source: SourceType
    description: Optional[str] = None
    working_hours: Optional[str] = None
    created_at: datetime
    needs_review: bool = False
    last_local_update_at: Optional[datetime] = None
    recyclemap_updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    statuses: List[EcoPointStatusRead] = []
    reviews: List[EcoPointReviewRead] = []

    class Config:
        from_attributes = True


class EcoPointUpdate(BaseModel):
    """Запрос на обновление данных эко-точки (от жителя)"""
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    type: Optional[EcoPointCategory] = None
    description: Optional[str] = None
    working_hours: Optional[str] = None

    class Config:
        from_attributes = True


class VisitCreate(BaseModel):
    """Пользователь отправляет посещение"""
    ecopoint_id: int
    proof_photo_url: str
    visited_at: datetime
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class VisitRead(BaseModel):
    id: int
    ecopoint_id: int
    proof_photo_url: str
    visited_at: datetime
    created_at: datetime
    comment: Optional[str] = None

    class Config:
        from_attributes = True
