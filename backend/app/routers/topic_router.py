"""
Topic and Topic Content Router.

Provides endpoints for viewing topic metadata and accessing educational content.
Enforces prerequisite locking rules and PostgreSQL caching to eliminate redundant AI calls.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.topic import Topic, TopicContent
from app.models.progress import TopicProgress
from app.auth.security import get_current_user
from app.schemas.topic_schema import TopicContentResponse, TopicDetailResponse
from app.schemas.map_schema import TopicProgressSummary
from app.services.ai_service import ai_service

router = APIRouter(prefix="/topics", tags=["Topics & Learning Content"])


@router.get(
    "/{topic_id}",
    response_model=TopicDetailResponse,
    summary="Get topic details and current progression status",
)
def get_topic_details(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves topic card information and the student's progress for this topic.
    Ensures that the requesting student owns the parent learning roadmap.
    """
    topic = db.scalar(select(Topic).where(Topic.id == topic_id))
    if not topic or topic.learning_map.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )

    progress = db.scalar(
        select(TopicProgress).where(
            TopicProgress.user_id == current_user.id,
            TopicProgress.topic_id == topic.id,
        )
    )

    prog_summary = None
    if progress:
        prog_summary = TopicProgressSummary(
            status=progress.status,
            mastery_score=progress.mastery_score,
            completed_at=progress.completed_at,
        )

    return TopicDetailResponse(
        id=topic.id,
        learning_map_id=topic.learning_map_id,
        goal_title=topic.learning_map.goal_title,
        title=topic.title,
        description=topic.description,
        sequence_order=topic.sequence_order,
        difficulty=topic.difficulty,
        estimated_minutes=topic.estimated_minutes,
        progress=prog_summary,
        has_content=topic.content is not None,
        content=TopicContentResponse.model_validate(topic.content) if topic.content else None,
    )


@router.get(
    "/{topic_id}/content",
    response_model=TopicContentResponse,
    summary="Get or generate educational content for a topic (Cached in PostgreSQL)",
)
def get_or_generate_topic_content(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves educational content for a topic:
    1. Verifies student ownership and prerequisite unlocked status.
    2. Checks PostgreSQL cache (TopicContent table) - returns immediately if cached.
    3. If cache miss: generates structured content via AI Service, saves to DB, and returns.
    4. Automatically advances topic progress from NOT_STARTED to IN_PROGRESS.
    """
    topic = db.scalar(select(Topic).where(Topic.id == topic_id))
    if not topic or topic.learning_map.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )

    # Check progression status
    progress = db.scalar(
        select(TopicProgress).where(
            TopicProgress.user_id == current_user.id,
            TopicProgress.topic_id == topic.id,
        )
    )

    if progress and progress.status == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This topic is currently locked. Complete the prerequisite topics and assessments first to unlock it.",
        )

    # 1. Check PostgreSQL Persistent Cache (REUSE RULE)
    cached_content = db.scalar(select(TopicContent).where(TopicContent.topic_id == topic.id))
    if cached_content:
        # Advance status if newly opened
        if progress and progress.status == "NOT_STARTED":
            progress.status = "IN_PROGRESS"
            db.commit()
        return cached_content

    # 2. Cache Miss: Generate with AI Service Layer
    profile = db.scalar(select(Profile).where(Profile.user_id == current_user.id))
    profile_context = None
    if profile:
        profile_context = {
            "current_skill_level": profile.current_skill_level,
            "preferred_learning_style": profile.preferred_learning_style,
        }

    ai_content = ai_service.generate_topic_content(
        topic_title=topic.title,
        goal_title=topic.learning_map.goal_title,
        profile_context=profile_context,
    )

    # 3. Persist to PostgreSQL topic_contents table
    new_content = TopicContent(
        topic_id=topic.id,
        summary=ai_content.summary,
        explanation=ai_content.explanation,
        code_examples=ai_content.code_examples,
        common_mistakes=ai_content.common_mistakes,
        key_takeaways=ai_content.key_takeaways,
    )
    db.add(new_content)

    # Advance status to IN_PROGRESS
    if progress and progress.status == "NOT_STARTED":
        progress.status = "IN_PROGRESS"

    db.commit()
    db.refresh(new_content)

    return new_content
