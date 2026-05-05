from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

from src.models.map import SourceType, PointStatus, EcoPointCategory


class EcoPointBase(BaseModel):
    """Базовые поля эко-точки"""
    name: str
    address: str
    latitude: float
    longitude: float
    type: EcoPointCategory


class EcoPointFilter(BaseModel):
    """Фильтры для карты (Use Case: просмотр точек на карте)"""
    type: Optional[EcoPointCategory] = None
    min_latitude: Optional[float] = None
    max_latitude: Optional[float] = None
    min_longitude: Optional[float] = None
    max_longitude: Optional[float] = None


class EcoPointCreate(EcoPointBase):
    """Создание новой точки (пользователем или организацией)"""
    description: Optional[str] = None
    working_hours: Optional[str] = None
    # recyclemap_id не указываем — он заполняется при синхронизации


class EcoPointRead(EcoPointBase):
    """Полная информация об эко-точке (для отображения на карте и в карточке)"""
    id: int
    recyclemap_id: Optional[str] = None
    source: SourceType                    # local или recyclemap
    local_status: Optional[PointStatus] = None
    status_confirmed_by: int = 0
    needs_review: bool = False
    created_at: datetime
    last_local_update_at: Optional[datetime] = None
    recyclemap_updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class EcoPointUpdate(BaseModel):
    """Редактирование точки (модератором или создателем)"""
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    working_hours: Optional[str] = None
    type: Optional[EcoPointCategory] = None


class EcoPointStatusCreate(BaseModel):
    """Пользователь ставит статус точки (работает / закрыто)"""
    status: PointStatus

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: PointStatus) -> PointStatus:
        return v


class EcoPointReviewCreate(BaseModel):
    """Создание отзыва + (опционально) статуса точки"""
    comment: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[PointStatus] = None   # можно одновременно поставить статус


class EcoPointReviewRead(BaseModel):
    """Отзыв для отображения"""
    id: int
    user_id: int
    comment: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[PointStatus] = None
    created_at: datetime

    class Config:
        from_attributes = True
