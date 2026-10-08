"""
Progress and Analytics Service.

Implements deterministic logic for tracking roadmap completion percentages,
auto-unlocking sequential prerequisites, calculating assessment statistics,
and generating explainable next-action recommendations.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.learning_map import LearningMap
from app.models.topic import Topic
from app.models.progress import TopicProgress
from app.models.assessment import AssessmentAttempt
from app.schemas.progress_schema import (
    DashboardAnalyticsResponse,
    CurrentTopicSummary,
)


def complete_topic_and_unlock_next(
    db: Session,
    user_id: str,
    topic_id: str,
    score: Optional[int] = None,
) -> TopicProgress:
    """
    Marks a topic as COMPLETED and automatically unlocks the immediate next topic in sequence.
    """
    topic = db.scalar(select(Topic).where(Topic.id == topic_id))
    if not topic or topic.learning_map.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )

    progress = db.scalar(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic.id,
        )
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress record not found for this topic.",
        )

    if progress.status == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete a locked topic. Prerequisites must be unlocked and studied first.",
        )

    # 1. Complete current topic
    progress.status = "COMPLETED"
    progress.completed_at = datetime.now(timezone.utc)
    if score is not None:
        progress.mastery_score = score

    # 2. Find and unlock the immediate next topic in this roadmap (N + 1)
    next_topic = db.scalar(
        select(Topic).where(
            Topic.learning_map_id == topic.learning_map_id,
            Topic.sequence_order == topic.sequence_order + 1,
        )
    )

    if next_topic:
        next_progress = db.scalar(
            select(TopicProgress).where(
                TopicProgress.user_id == user_id,
                TopicProgress.topic_id == next_topic.id,
            )
        )
        if next_progress and next_progress.status == "LOCKED":
            next_progress.status = "NOT_STARTED"

    db.commit()
    db.refresh(progress)
    return progress


def calculate_dashboard_analytics(db: Session, user_id: str) -> DashboardAnalyticsResponse:
    """
    Aggregates learning metrics purely through deterministic backend computation:
    - Overall completion percentage
    - Completed / Total topics count
    - Next actionable topic for "Continue Learning"
    - Average assessment score
    - Aggregated weak areas list
    - Explainable recommendation rationale
    """
    lmap = db.scalar(
        select(LearningMap).where(
            LearningMap.user_id == user_id,
            LearningMap.is_active == True,
        )
    )
    if not lmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active learning roadmap found. Please generate a roadmap first to view dashboard analytics.",
        )

    topics = sorted(lmap.topics, key=lambda t: t.sequence_order)
    topic_ids = [t.id for t in topics]

    progress_records = db.scalars(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id.in_(topic_ids),
        )
    ).all()
    progress_map: Dict[str, TopicProgress] = {p.topic_id: p for p in progress_records}

    # 1. Count completion metrics
    total_topics = len(topics)
    completed_topics = sum(1 for p in progress_records if p.status == "COMPLETED")
    overall_percentage = int((completed_topics / total_topics) * 100) if total_topics > 0 else 0

    # 2. Resolve "Continue Learning" current actionable topic
    # Priority: First IN_PROGRESS topic, else first NOT_STARTED topic
    current_topic_obj: Optional[Topic] = None
    current_status: Optional[str] = None

    for t in topics:
        p = progress_map.get(t.id)
        if p and p.status == "IN_PROGRESS":
            current_topic_obj = t
            current_status = "IN_PROGRESS"
            break

    if not current_topic_obj:
        for t in topics:
            p = progress_map.get(t.id)
            if p and p.status == "NOT_STARTED":
                current_topic_obj = t
                current_status = "NOT_STARTED"
                break

    current_topic_summary = None
    if current_topic_obj and current_status:
        current_topic_summary = CurrentTopicSummary(
            topic_id=current_topic_obj.id,
            sequence_order=current_topic_obj.sequence_order,
            title=current_topic_obj.title,
            difficulty=current_topic_obj.difficulty,
            status=current_status,
        )

    # 3. Aggregate Assessment Attempts & Weak Areas
    attempts = db.scalars(
        select(AssessmentAttempt).where(AssessmentAttempt.user_id == user_id)
    ).all()

    avg_score = None
    weak_areas_set = set()
    if attempts:
        avg_score = round(sum(a.score_percentage for a in attempts) / len(attempts), 1)
        for a in attempts:
            if a.weak_areas and isinstance(a.weak_areas, list):
                for w in a.weak_areas:
                    weak_areas_set.add(str(w))

    # 4. Generate Explainable Recommendation & Level Completion Status
    current_level = (getattr(lmap, "learning_level", "beginner") or "beginner").lower()
    is_level_completed = (completed_topics == total_topics and total_topics > 0)
    next_level_map = {
        "beginner": "intermediate",
        "intermediate": "advanced",
    }
    next_level_available = next_level_map.get(current_level) if is_level_completed else None
    next_level_goal = lmap.goal_title if next_level_available else None

    if current_topic_summary:
        if current_status == "IN_PROGRESS":
            reason = f"Recommended because you started '{current_topic_summary.title}' and it is your active topic in the {current_level.capitalize()} '{lmap.goal_title}' journey."
        else:
            reason = f"Recommended because '{current_topic_summary.title}' is your next unlocked prerequisite topic in the {current_level.capitalize()} '{lmap.goal_title}' journey."
    elif is_level_completed:
        if next_level_available:
            reason = f"🎉 Congratulations! Outstanding achievement! You completed 100% of your {current_level.capitalize()} '{lmap.goal_title}' roadmap. Ready to advance to {next_level_available.capitalize()} level!"
        else:
            reason = f"🏆 Congratulations! Mastery achieved! You have completed all {total_topics} topics in the Advanced '{lmap.goal_title}' journey."
    else:
        reason = "Select a topic card to begin your learning journey."

    return DashboardAnalyticsResponse(
        active_roadmap_id=lmap.id,
        goal_title=lmap.goal_title,
        learning_level=current_level,
        overall_progress_percentage=overall_percentage,
        completed_topics_count=completed_topics,
        total_topics_count=total_topics,
        current_topic=current_topic_summary,
        average_score=avg_score,
        total_weak_areas_count=len(weak_areas_set),
        weak_areas_summary=sorted(list(weak_areas_set)),
        recommendation_reason=reason,
        is_level_completed=is_level_completed,
        next_level_available=next_level_available,
        next_level_goal=next_level_goal,
    )
