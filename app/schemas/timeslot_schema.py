from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TimeSlotBase(BaseModel):
    service_id: int
    trainer_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    capacity: int


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlotRead(TimeSlotBase):
    id: int

    class Config:
        from_attributes = True