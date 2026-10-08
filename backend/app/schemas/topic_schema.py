"""
Topic and TopicContent Request and Response Schemas.

Defines Pydantic models for educational materials, code examples,
and detailed topic status information.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.map_schema import TopicProgressSummary


class TopicContentResponse(BaseModel):
    """Structured educational content persisted for a topic."""
    id: str
    topic_id: str
    summary: str
    explanation: str
    code_examples: str
    common_mistakes: str
    key_takeaways: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicDetailResponse(BaseModel):
    """Detailed topic overview with attached progress and content."""
    id: str
    learning_map_id: str
    goal_title: str
    title: str
    description: str
    sequence_order: int
    difficulty: str
    estimated_minutes: int
    progress: Optional[TopicProgressSummary] = None
    has_content: bool = False
    content: Optional[TopicContentResponse] = None

    model_config = ConfigDict(from_attributes=True)
