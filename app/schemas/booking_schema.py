from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone

from . import UserRead, TimeSlotRead


class BookingBase(BaseModel):
    user_id: int
    time_slot_id: int


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    status: str
    created_at: datetime

    user: Optional[UserRead] = None
    time_slot: Optional[TimeSlotRead] = None

    class Config:
        from_attributes = True
