"""
Profile Request and Response Schemas.

Defines Pydantic models for student learning profile intake, updates, and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProfileCreateRequest(BaseModel):
    """Schema for initializing student learning profile."""
    education_level: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="e.g. Undergraduate, High School, Working Professional",
        json_schema_extra={"example": "3rd Year CSE Undergraduate"},
    )
    target_goal: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Career or learning goal",
        json_schema_extra={"example": "Java Backend Developer"},
    )
    current_skill_level: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Baseline skill level: Beginner, Intermediate, or Advanced",
        json_schema_extra={"example": "Beginner"},
    )
    weekly_hours_available: int = Field(
        10,
        ge=1,
        le=80,
        description="Estimated weekly learning hours (1 to 80)",
        json_schema_extra={"example": 12},
    )
    preferred_learning_style: str = Field(
        "Practical",
        min_length=2,
        max_length=100,
        description="Preferred style: Practical, Theoretical, Visual, etc.",
        json_schema_extra={"example": "Practical / Hands-on"},
    )


class ProfileUpdateRequest(BaseModel):
    """Schema for updating an existing student profile."""
    education_level: Optional[str] = Field(None, min_length=2, max_length=100)
    target_goal: Optional[str] = Field(None, min_length=2, max_length=200)
    current_skill_level: Optional[str] = Field(None, min_length=2, max_length=50)
    weekly_hours_available: Optional[int] = Field(None, ge=1, le=80)
    preferred_learning_style: Optional[str] = Field(None, min_length=2, max_length=100)


class ProfileResponse(BaseModel):
    """Schema for returning student profile details."""
    id: str
    user_id: str
    education_level: str
    target_goal: str
    current_skill_level: str
    weekly_hours_available: int
    preferred_learning_style: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
