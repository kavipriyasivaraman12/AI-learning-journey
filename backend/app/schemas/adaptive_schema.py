"""
Adaptive Learning Pydantic Schemas.

Defines schemas for adaptive learning recommendations, targeted weak-area guidance,
and next-step progression decisions based on student assessment performance.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class WeakAreaGuidance(BaseModel):
    """Targeted learning guidance for a specific weak concept."""
    concept_name: str = Field(..., description="Concept or question missed")
    recommendation: str = Field(..., description="Actionable advice to master this concept")

    model_config = ConfigDict(from_attributes=True)


class AdaptiveRecommendationResponse(BaseModel):
    """Personalized adaptive learning recommendation after assessment evaluation."""
    topic_id: str = Field(..., description="Current topic UUID")
    topic_title: str = Field(..., description="Current topic title")
    assessment_id: str = Field(..., description="Assessment UUID")
    attempt_id: Optional[str] = Field(None, description="Latest attempt UUID if available")
    score_percentage: int = Field(..., description="Student assessment score percentage")
    passing_score_percentage: int = Field(..., description="Passing threshold percentage")
    passed: bool = Field(..., description="Whether student met the mastery threshold")
    action: str = Field(..., description="Recommended action: PROCEED_TO_NEXT_TOPIC, REVIEW_AND_RETAKE, COMPLETE_ROADMAP")
    reason: str = Field(..., description="Explainable reason for this recommendation")
    next_step: str = Field(..., description="Concrete next actionable step")
    next_topic_id: Optional[str] = Field(None, description="UUID of the next topic if unlocked")
    next_topic_title: Optional[str] = Field(None, description="Title of the next topic if unlocked")
    weak_areas_guidance: List[WeakAreaGuidance] = Field(default_factory=list, description="Targeted guidance for weak areas")

    model_config = ConfigDict(from_attributes=True)
