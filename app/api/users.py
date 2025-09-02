from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.get("/", response_model=List[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get list of all users (admin only)"""
    result = await db.execute(select(User))
    return list(result.scalars().all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
