from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    role: str
    created_at: datetime
    bookings:list
    is_active: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AboutMe(BaseModel):
    id: int
    name: str
    email:EmailStr
    bookings:list

class Role(BaseModel):
    user_role: str = "user"