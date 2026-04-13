from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone


class ServiceBase(BaseModel):
    name: str
    description: Optional[str]
    duration_minutes: int
    capacity: int
    price: float


class ServiceCreate(ServiceBase):
    pass


class ServiceRead(ServiceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
