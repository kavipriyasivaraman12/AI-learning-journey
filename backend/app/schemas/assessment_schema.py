"""
Assessment and Quiz Pydantic Schemas.

Defines schemas for requesting assessments, submitting answers, and evaluating
student quiz attempts with detailed score breakdown and weak area analysis.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AssessmentQuestionStudentView(BaseModel):
    """Student-facing view of a quiz question (correct answer omitted)."""
    id: str = Field(..., description="Unique question UUID")
    question_text: str = Field(..., description="The multiple choice question")
    options: List[str] = Field(..., description="Available answer choices")

    model_config = ConfigDict(from_attributes=True)


class AssessmentResponse(BaseModel):
    """Student-facing topic assessment quiz."""
    id: str = Field(..., description="Assessment UUID")
    topic_id: str = Field(..., description="Topic UUID evaluated")
    title: str = Field(..., description="Assessment title")
    passing_score_percentage: int = Field(..., description="Required passing percentage")
    questions: List[AssessmentQuestionStudentView] = Field(..., description="List of questions")

    model_config = ConfigDict(from_attributes=True)


class AssessmentSubmitAnswer(BaseModel):
    """A single submitted answer for a question."""
    question_id: str = Field(..., description="Question UUID")
    selected_option_index: int = Field(..., ge=0, description="0-indexed chosen option")


class AssessmentSubmitRequest(BaseModel):
    """Submission payload containing student answers."""
    answers: List[AssessmentSubmitAnswer] = Field(..., min_length=1, description="List of answers")
    selected_question_ids: Optional[List[str]] = Field(
        default=None,
        description="IDs of the 15 questions shown to the student this attempt (for retake randomization)"
    )


class QuestionResult(BaseModel):
    """Detailed evaluation result for an individual question."""
    question_id: str = Field(..., description="Question UUID")
    question_text: str = Field(..., description="Question prompt")
    options: List[str] = Field(..., description="Question options")
    selected_option_index: int = Field(..., description="Index selected by student")
    correct_option_index: int = Field(..., description="Correct answer index")
    is_correct: bool = Field(..., description="Whether answer was correct")
    explanation: str = Field(..., description="Educational explanation")
    concept_tag: Optional[str] = Field(None, description="Concept tested")


from app.schemas.adaptive_schema import AdaptiveRecommendationResponse


class AssessmentAttemptResponse(BaseModel):
    """Complete scorecard and analysis for an assessment attempt."""
    id: str = Field(..., description="Attempt UUID")
    assessment_id: str = Field(..., description="Assessment UUID")
    user_id: str = Field(..., description="Student UUID")
    score_percentage: int = Field(..., description="Calculated score (0-100%)")
    passed: bool = Field(..., description="Whether passing threshold was met")
    passing_score_percentage: int = Field(..., description="Required passing percentage")
    total_questions: int = Field(..., description="Total questions on quiz")
    correct_answers_count: int = Field(..., description="Number of correct answers")
    weak_areas: List[str] = Field(default_factory=list, description="List of identified weak concepts")
    attempted_at: datetime = Field(..., description="Timestamp of submission")
    question_results: Optional[List[QuestionResult]] = Field(None, description="Review of all questions")
    adaptive_recommendation: Optional[AdaptiveRecommendationResponse] = Field(
        None, description="Adaptive learning guidance and next-step progression decision"
    )

    model_config = ConfigDict(from_attributes=True)




class AssessmentAttemptHistoryItem(BaseModel):
    """Summary item for assessment attempt history list."""
    id: str
    assessment_id: str
    score_percentage: int
    passed: bool
    weak_areas: List[str]
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)
