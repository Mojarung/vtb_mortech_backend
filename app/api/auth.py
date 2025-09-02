from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User
from app.schemas.user import UserCreate, UserRead, UserUpdate, Token
from app.services.security import create_access_token, get_password_hash, verify_password
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    existing_email = await db.execute(select(User).where(User.email == user_in.email))
    if existing_email.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Check if username already exists
    existing_username = await db.execute(select(User).where(User.username == user_in.username))
    if existing_username.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    # Create new user with all fields
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        about=user_in.about,
        phone=user_in.phone,
        birth_date=user_in.birth_date,
        skills=user_in.skills,
        education=user_in.education
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Find user by username or email
    user = await db.execute(
        select(User).where(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
    )
    user = user.scalar_one_or_none()
    
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username/email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User account is disabled")

    token = create_access_token(subject=user.id)
    return Token(access_token=token)


@router.put("/me", response_model=UserRead)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check email uniqueness if changing
    if user_update.email and user_update.email != current_user.email:
        existing = await db.execute(select(User).where(User.email == user_update.email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")

    # Check username uniqueness if changing
    if user_update.username and user_update.username != current_user.username:
        existing = await db.execute(select(User).where(User.username == user_update.username))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user
