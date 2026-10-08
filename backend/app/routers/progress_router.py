"""
Progress and Dashboard Analytics Router.

Provides endpoints for fetching student dashboard analytics and
advancing topic completion states with automatic prerequisite unlocking.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.security import get_current_user
from app.schemas.progress_schema import (
    DashboardAnalyticsResponse,
    TopicCompleteRequest,
)
from app.schemas.map_schema import TopicProgressSummary
from app.services.progress_service import (
    calculate_dashboard_analytics,
    complete_topic_and_unlock_next,
)

router = APIRouter(tags=["Progress & Dashboard"])


@router.get(
    "/progress/dashboard",
    response_model=DashboardAnalyticsResponse,
    summary="Get aggregated dashboard statistics and active journey progress",
)
def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes overall completion percentage, topics completed, average assessment score,
    total weak areas, and the actionable topic for the 'Continue Learning' button.
    """
    return calculate_dashboard_analytics(db, current_user.id)


@router.post(
    "/topics/{topic_id}/complete",
    response_model=TopicProgressSummary,
    summary="Mark topic completed and unlock next sequential topic",
)
def mark_topic_complete(
    topic_id: str,
    request: Optional[TopicCompleteRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sets the specified topic's status to COMPLETED and automatically unlocks
    the immediate next topic (N + 1) in the learning roadmap from LOCKED to NOT_STARTED.
    """
    score = request.mastery_score if request else None
    progress = complete_topic_and_unlock_next(
        db=db,
        user_id=current_user.id,
        topic_id=topic_id,
        score=score,
    )
    return TopicProgressSummary.model_validate(progress)
