"""
AI Topic Tutor Pydantic Schemas.

Defines schemas for sending student topic-related questions and receiving
personalized explanations, code snippets, common pitfalls, and practice questions.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TutorHistoryItem(BaseModel):
    """Previous chat message in conversation."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class TopicTutorRequest(BaseModel):
    """Student question payload for the topic AI tutor."""
    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="The student's technical question or clarification about the topic",
        json_schema_extra={"example": "Can you explain how method overriding works with a real-world analogy?"},
    )
    conversation_history: Optional[List[TutorHistoryItem]] = Field(
        default=None,
        description="Optional list of prior messages in the conversation for multi-turn context",
    )

    @field_validator("question")
    def validate_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Question cannot be empty or solely whitespace.")
        return stripped


class TopicTutorResponse(BaseModel):
    """AI Tutor personalized answer and guidance."""
    topic_id: str = Field(..., description="UUID of the topic being studied")
    topic_title: str = Field(..., description="Title of the topic")
    student_skill_level: str = Field(..., description="The learner's current skill level")
    question: str = Field(..., description="Original question asked")
    explanation: str = Field(..., description="Beginner-friendly pedagogical explanation")
    code_example: Optional[str] = Field(None, description="Illustrative code example")
    common_mistake: Optional[str] = Field(None, description="Related common mistake or anti-pattern")
    practice_question: Optional[str] = Field(None, description="Short self-check challenge")
    is_topic_related: bool = Field(True, description="Whether the question was related to the current topic")

    model_config = ConfigDict(from_attributes=True)
