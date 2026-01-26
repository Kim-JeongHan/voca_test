# -*- coding: utf-8 -*-
"""Authentication API endpoints."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    create_access_token,
    get_current_user_required,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists (if provided)
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token."""
    # Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create access token
    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expire_hours * 3600,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user_required)):
    """Get current user information."""
    return current_user


@router.post("/password-reset", status_code=status.HTTP_200_OK)
def request_password_reset(
    reset_data: PasswordResetRequest, db: Session = Depends(get_db)
):
    """Request a password reset token."""
    # Find user by email
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        # Don't reveal if email exists - return success anyway
        return {"message": "If the email exists, a reset link has been sent"}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    # In production, send email with reset link
    # For now, just return the token (for testing)
    if settings.debug:
        return {"message": "Reset token generated", "reset_token": reset_token}

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(
    confirm_data: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Confirm password reset with token."""
    # Find user by reset token
    user = db.query(User).filter(User.reset_token == confirm_data.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if token is expired
    if user.reset_token_expires and user.reset_token_expires < datetime.now(
        timezone.utc
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Update password
    user.password_hash = hash_password(confirm_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password has been reset successfully"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """Change password for logged-in user."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}
