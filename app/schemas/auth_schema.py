from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str
