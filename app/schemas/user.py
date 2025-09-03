from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    about: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    is_hr: bool = False
    company: Optional[str] = None
    position: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    about: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    is_hr: Optional[bool] = None
    company: Optional[str] = None
    position: Optional[str] = None


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
