"""
Learning Map Request and Response Schemas.

Defines Pydantic models for roadmaps, topics, and topic progress summaries.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicProgressSummary(BaseModel):
    """Summarized progress state for a topic."""
    status: str = "LOCKED"  # LOCKED, NOT_STARTED, IN_PROGRESS, COMPLETED
    mastery_score: int = 0
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TopicSummaryResponse(BaseModel):
    """Topic card details with attached progress state."""
    id: str
    learning_map_id: str
    title: str
    description: str
    sequence_order: int
    difficulty: str
    estimated_minutes: int
    progress: Optional[TopicProgressSummary] = None

    model_config = ConfigDict(from_attributes=True)


class LearningMapCreateRequest(BaseModel):
    """Schema to generate or request a learning roadmap."""
    goal_title: Optional[str] = Field(
        None,
        description="Target subject or career goal. If omitted, uses student's profile goal.",
        json_schema_extra={"example": "Java Backend Developer"},
    )
    learning_level: Optional[str] = Field(
        None,
        description="Target skill level: beginner, intermediate, or advanced. If omitted, uses profile skill level.",
        json_schema_extra={"example": "beginner"},
    )
    force_regenerate: bool = Field(
        False,
        description="If True, forces generation of a new roadmap even if an existing one is active.",
    )


class LearningMapResponse(BaseModel):
    """Full learning map response with all topic cards and progress."""
    id: str
    user_id: str
    goal_title: str
    learning_level: str = "beginner"
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    topics: List[TopicSummaryResponse] = []

    model_config = ConfigDict(from_attributes=True)


class LearningMapListItem(BaseModel):
    """Brief summary item for listing all maps of a student."""
    id: str
    goal_title: str
    learning_level: str = "beginner"
    description: str
    is_active: bool
    total_topics: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
