from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str
    email: EmailStr
    about: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    is_active: bool = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6)
    about: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skills: Optional[str] = None
    education: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=150)
    email: Optional[EmailStr] = None
    about: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skills: Optional[str] = None
    education: Optional[str] = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
