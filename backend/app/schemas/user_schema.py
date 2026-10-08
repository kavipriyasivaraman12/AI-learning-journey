"""
User Request and Response Schemas.

Defines Pydantic models for user registration, login, and profile responses.
Ensures strict validation of input data formats.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    """Schema for student registration request."""
    email: EmailStr = Field(..., description="Valid student email address", json_schema_extra={"example": "student@example.com"})
    password: str = Field(..., min_length=8, max_length=100, description="Password (at least 8 characters)", json_schema_extra={"example": "SecurePass123"})
    full_name: str = Field(..., min_length=2, max_length=150, description="Student full name", json_schema_extra={"example": "Kavipriya S"})


class UserLoginRequest(BaseModel):
    """Schema for student login credentials."""
    email: EmailStr = Field(..., description="Registered email address", json_schema_extra={"example": "student@example.com"})
    password: str = Field(..., min_length=1, description="Account password", json_schema_extra={"example": "SecurePass123"})


class UserResponse(BaseModel):
    """Schema for returning user data (never includes password)."""
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for returning JWT authentication token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Internal schema for decoded JWT token payload."""
    sub: str  # User ID
    email: Optional[str] = None
    exp: Optional[int] = None
