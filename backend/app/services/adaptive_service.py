"""
Adaptive Learning Decision Service.

Implements deterministic rule-based adaptive decisions:
1. Evaluates student assessment performance against passing thresholds.
2. Formulates targeted revision recommendations for specific weak areas.
3. Automatically completes topics and unlocks next prerequisites when mastery is demonstrated.
4. Keeps subsequent topics locked when performance is below threshold and provides actionable remediation guidance.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.topic import Topic
from app.models.progress import TopicProgress
from app.models.assessment import Assessment, AssessmentAttempt
from app.schemas.adaptive_schema import (
    AdaptiveRecommendationResponse,
    WeakAreaGuidance,
)


def generate_adaptive_recommendation(
    db: Session,
    user_id: str,
    topic_id: str,
    attempt: Optional[AssessmentAttempt] = None,
) -> AdaptiveRecommendationResponse:
    """
    Computes explainable adaptive guidance based on the student's assessment performance
    and weak areas on a specific topic.
    """
    topic = db.scalar(select(Topic).where(Topic.id == topic_id))
    if not topic or topic.learning_map.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )

    assessment = db.scalar(select(Assessment).where(Assessment.topic_id == topic.id))
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment for this topic has not been generated yet.",
        )

    # If no attempt was passed in directly, find the latest attempt
    if not attempt:
        attempt = db.scalar(
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.user_id == user_id,
            )
            .order_by(AssessmentAttempt.attempted_at.desc())
        )

    # Find the immediate next topic in sequence
    next_topic = db.scalar(
        select(Topic).where(
            Topic.learning_map_id == topic.learning_map_id,
            Topic.sequence_order == topic.sequence_order + 1,
        )
    )

    # Build targeted guidance for each weak area
    weak_areas = attempt.weak_areas if (attempt and attempt.weak_areas) else []
    weak_guidance_list: List[WeakAreaGuidance] = []
    for wa in weak_areas:
        weak_guidance_list.append(
            WeakAreaGuidance(
                concept_name=str(wa),
                recommendation=(
                    f"Re-read the explanation, study the annotated code examples, and review common mistakes "
                    f"in '{topic.title}' for '{wa}'."
                ),
            )
        )

    # Determine adaptive action, reason, and next step
    if attempt:
        score_pct = attempt.score_percentage
        passing_pct = assessment.passing_score_percentage
        passed = attempt.passed

        if passed:
            if next_topic:
                action = "PROCEED_TO_NEXT_TOPIC"
                reason = (
                    f"Mastery confirmed! You scored {score_pct}% (pass threshold: {passing_pct}%). "
                    f"'{topic.title}' is marked completed and '{next_topic.title}' has been unlocked."
                )
                next_step = f"Advance to '{next_topic.title}' to continue your learning journey."
            else:
                action = "COMPLETE_ROADMAP"
                reason = (
                    f"Outstanding! You scored {score_pct}% on the final topic and completed 100% of your "
                    f"'{topic.learning_map.goal_title}' learning roadmap."
                )
                next_step = "Celebrate your achievement or review your full dashboard statistics."
        else:
            action = "REVIEW_AND_RETAKE"
            reason = (
                f"Your score of {score_pct}% is below the required {passing_pct}% mastery mark. "
                f"The next topic remains locked to ensure prerequisite knowledge is solidified before moving forward."
            )
            next_step = (
                f"Review the topic material focusing on your {len(weak_areas)} identified weak areas, "
                f"then retake the assessment to demonstrate mastery."
            )
    else:
        # Default when no attempt exists yet
        score_pct = 0
        passing_pct = assessment.passing_score_percentage
        passed = False
        action = "TAKE_ASSESSMENT"
        reason = f"Complete the mastery assessment for '{topic.title}' to test your skills and unlock the next topic."
        next_step = f"Take the assessment quiz for '{topic.title}'."

    return AdaptiveRecommendationResponse(
        topic_id=topic.id,
        topic_title=topic.title,
        assessment_id=assessment.id,
        attempt_id=attempt.id if attempt else None,
        score_percentage=score_pct,
        passing_score_percentage=passing_pct,
        passed=passed,
        action=action,
        reason=reason,
        next_step=next_step,
        next_topic_id=next_topic.id if (next_topic and passed) else None,
        next_topic_title=next_topic.title if (next_topic and passed) else None,
        weak_areas_guidance=weak_guidance_list,
    )
