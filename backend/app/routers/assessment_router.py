"""
Assessment and Quiz Router.

Provides endpoints for retrieving topic mastery assessments (with PostgreSQL caching),
submitting answers for objective evaluation, logging attempts, and analyzing weak areas.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.assessment import Assessment, AssessmentAttempt
from app.auth.security import get_current_user
from app.schemas.assessment_schema import (
    AssessmentResponse,
    AssessmentQuestionStudentView,
    AssessmentSubmitRequest,
    AssessmentAttemptResponse,
    AssessmentAttemptHistoryItem,
)
from app.schemas.adaptive_schema import AdaptiveRecommendationResponse
from app.services.assessment_service import (
    get_or_create_topic_assessment,
    evaluate_assessment_submission,
)
from app.services.adaptive_service import generate_adaptive_recommendation


router = APIRouter(tags=["Assessments & Quizzes"])


@router.get(
    "/topics/{topic_id}/assessment",
    response_model=AssessmentResponse,
    summary="Get or generate assessment quiz for a topic (Cached in PostgreSQL)",
)
def get_topic_assessment(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves or generates the mastery quiz for a specific topic:
    1. Enforces student ownership and prerequisite unlock status.
    2. Checks PostgreSQL cache — returns existing assessment if available.
    3. If cache miss, generates structured quiz with AI Service and persists to DB.
    4. Omits correct answers so questions can be presented safely to the student.
    """
    assessment, selected_questions = get_or_create_topic_assessment(
        db=db,
        topic_id=topic_id,
        current_user_id=current_user.id,
    )

    student_questions = [
        AssessmentQuestionStudentView(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
        )
        for q in selected_questions
    ]

    return AssessmentResponse(
        id=assessment.id,
        topic_id=assessment.topic_id,
        title=assessment.title,
        passing_score_percentage=assessment.passing_score_percentage,
        questions=student_questions,
    )


@router.post(
    "/assessments/{assessment_id}/submit",
    response_model=AssessmentAttemptResponse,
    summary="Submit answers for evaluation and score calculation",
)
def submit_assessment(
    assessment_id: str,
    submission: AssessmentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates student quiz answers against ground-truth options:
    1. Verifies ownership of the assessment.
    2. Calculates total score percentage.
    3. Determines pass/fail status based on passing threshold.
    4. Detects specific weak areas corresponding to incorrect answers.
    5. Logs attempt in PostgreSQL and updates topic mastery score.
    6. Returns complete question review and feedback.
    """
    return evaluate_assessment_submission(
        db=db,
        assessment_id=assessment_id,
        current_user_id=current_user.id,
        answers=submission.answers,
        selected_question_ids=getattr(submission, 'selected_question_ids', None),
    )


@router.get(
    "/assessments/{assessment_id}/attempts",
    response_model=List[AssessmentAttemptHistoryItem],
    summary="Get attempt history for an assessment",
)
def get_assessment_attempts(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all previous attempts made by the student for this assessment.
    """
    assessment = db.scalar(select(Assessment).where(Assessment.id == assessment_id))
    if not assessment or assessment.topic.learning_map.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    attempts = db.scalars(
        select(AssessmentAttempt)
        .where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == current_user.id,
        )
        .order_by(AssessmentAttempt.attempted_at.desc())
    ).all()

    return [
        AssessmentAttemptHistoryItem(
            id=att.id,
            assessment_id=att.assessment_id,
            score_percentage=att.score_percentage,
            passed=att.passed,
            weak_areas=att.weak_areas or [],
            attempted_at=att.attempted_at,
        )
        for att in attempts
    ]


@router.get(
    "/topics/{topic_id}/adaptive-recommendation",
    response_model=AdaptiveRecommendationResponse,
    summary="Get adaptive learning recommendation and next-step decisions for a topic",
)
def get_topic_adaptive_recommendation(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns explainable adaptive guidance based on the student's latest assessment attempt:
    1. Recommends proceeding to the next topic if mastery was demonstrated.
    2. Recommends targeted weak area practice and quiz retake if score was below threshold.
    3. Explains why the decision was made.
    """
    return generate_adaptive_recommendation(
        db=db,
        user_id=current_user.id,
        topic_id=topic_id,
    )

