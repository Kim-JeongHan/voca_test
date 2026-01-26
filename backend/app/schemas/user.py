# -*- coding: utf-8 -*-
"""Pydantic schemas for user authentication."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    """Schema for user response (public info only)."""

    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordChange(BaseModel):
    """Schema for password change (when logged in)."""

    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
