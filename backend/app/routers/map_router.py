"""
Learning Map Router.

Provides REST endpoints for generating, fetching, and managing student learning roadmaps.
All endpoints require JWT Bearer authentication.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.learning_map import LearningMap
from app.models.topic import Topic
from app.models.progress import TopicProgress
from app.auth.security import get_current_user
from app.schemas.map_schema import (
    LearningMapCreateRequest,
    LearningMapResponse,
    LearningMapListItem,
)
from app.services.learning_service import (
    get_or_create_learning_map,
    build_learning_map_response,
)

router = APIRouter(prefix="/learning-maps", tags=["Learning Maps"])


@router.post(
    "",
    response_model=LearningMapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate or retrieve active personalized learning map",
)
def generate_or_get_map(
    request: LearningMapCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new learning map or reuses an existing active one for the target goal and level.
    Initializes topic progression cards (Topic 1: NOT_STARTED, Topics 2+: LOCKED).
    """
    lmap = get_or_create_learning_map(
        db=db,
        user=current_user,
        goal_title=request.goal_title,
        learning_level=request.learning_level,
        force_regenerate=request.force_regenerate,
    )
    return build_learning_map_response(db, lmap, current_user.id)


@router.post(
    "/next-level",
    response_model=LearningMapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Advance to next learning level journey (e.g., Beginner -> Intermediate -> Advanced)",
)
def advance_to_next_level(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Advances a student who completed their active roadmap to the next sequential skill level:
    - Beginner -> Intermediate
    - Intermediate -> Advanced
    """
    active_map = db.scalar(
        select(LearningMap).where(
            LearningMap.user_id == current_user.id,
            LearningMap.is_active == True,
        )
    )
    if not active_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active learning journey found to advance from.",
        )

    current_level = (getattr(active_map, "learning_level", "beginner") or "beginner").lower()

    # Verify all topics in active roadmap are completed before advancing
    topics = db.scalars(
        select(Topic).where(Topic.learning_map_id == active_map.id)
    ).all()
    if topics:
        topic_ids = [t.id for t in topics]
        progress_records = db.scalars(
            select(TopicProgress).where(
                TopicProgress.user_id == current_user.id,
                TopicProgress.topic_id.in_(topic_ids),
            )
        ).all()
        completed_count = sum(1 for p in progress_records if p.status == "COMPLETED")
        if completed_count < len(topics):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot advance yet. You have completed {completed_count} of {len(topics)} topics in your {current_level.capitalize()} roadmap.",
            )

    next_level_map = {
        "beginner": "intermediate",
        "intermediate": "advanced",
    }
    next_level = next_level_map.get(current_level)
    if not next_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have already completed the highest tier ({current_level.capitalize()}) for this journey.",
        )

    new_map = get_or_create_learning_map(
        db=db,
        user=current_user,
        goal_title=active_map.goal_title,
        learning_level=next_level,
        force_regenerate=True,
    )
    return build_learning_map_response(db, new_map, current_user.id)


@router.get(
    "/active",
    response_model=LearningMapResponse,
    summary="Get current active learning roadmap",
)
def get_active_roadmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetches the student's currently active learning roadmap with topic cards and progress status.
    """
    lmap = db.scalar(
        select(LearningMap).where(
            LearningMap.user_id == current_user.id,
            LearningMap.is_active == True,
        )
    )
    if not lmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active learning roadmap found. Please generate a roadmap first.",
        )
    return build_learning_map_response(db, lmap, current_user.id)


@router.get(
    "/{map_id}",
    response_model=LearningMapResponse,
    summary="Get learning roadmap by ID",
)
def get_roadmap_by_id(
    map_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetches a specific roadmap by ID, ensuring user ownership isolation.
    """
    lmap = db.scalar(
        select(LearningMap).where(
            LearningMap.id == map_id,
            LearningMap.user_id == current_user.id,
        )
    )
    if not lmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning roadmap not found.",
        )
    return build_learning_map_response(db, lmap, current_user.id)


@router.get(
    "",
    response_model=List[LearningMapListItem],
    summary="List all learning roadmaps for student",
)
def list_student_roadmaps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns an overview list of all roadmaps generated by the authenticated student.
    """
    maps = db.scalars(
        select(LearningMap)
        .where(LearningMap.user_id == current_user.id)
        .order_by(LearningMap.created_at.desc())
    ).all()

    return [
        LearningMapListItem(
            id=m.id,
            goal_title=m.goal_title,
            description=m.description,
            is_active=m.is_active,
            total_topics=len(m.topics),
            created_at=m.created_at,
        )
        for m in maps
    ]
