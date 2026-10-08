"""
Progress and Dashboard Analytics Schemas.

Defines Pydantic models for tracking topic completions, roadmap percentages,
current topic resolution for the Continue Learning action, and explainable recommendations.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CurrentTopicSummary(BaseModel):
    """Details of the student's current actionable topic."""
    topic_id: str
    sequence_order: int
    title: str
    difficulty: str
    status: str  # NOT_STARTED or IN_PROGRESS

    model_config = ConfigDict(from_attributes=True)


class DashboardAnalyticsResponse(BaseModel):
    """Aggregate statistics and insights for the Student Dashboard."""
    active_roadmap_id: str
    goal_title: str
    learning_level: str = "beginner"
    overall_progress_percentage: int = Field(0, ge=0, le=100)
    completed_topics_count: int
    total_topics_count: int
    current_topic: Optional[CurrentTopicSummary] = None
    average_score: Optional[float] = None
    total_weak_areas_count: int = 0
    weak_areas_summary: List[str] = []
    recommendation_reason: str = Field(..., description="Explainable rationale for the next recommended step")
    is_level_completed: bool = Field(False, description="Whether all topics in current journey have been completed")
    next_level_available: Optional[str] = Field(None, description="Next learning level (intermediate or advanced) if completed")
    next_level_goal: Optional[str] = Field(None, description="Target goal for the next level")

    model_config = ConfigDict(from_attributes=True)


class TopicCompleteRequest(BaseModel):
    """Optional request payload when manually marking a topic completed."""
    mastery_score: Optional[int] = Field(None, ge=0, le=100, description="Optional manual self-assessment score")
