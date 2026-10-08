"""
Learning Profile Router.

Provides endpoints for creating, retrieving, and updating a student's learning profile.
All endpoints require JWT Bearer authentication and operate strictly on the logged-in user's profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.auth.security import get_current_user
from app.schemas.profile_schema import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
)

router = APIRouter(prefix="/profile", tags=["Learning Profile"])


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get current student learning profile",
)
def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the learning profile for the authenticated student.
    Returns HTTP 404 if the student has not yet configured their profile.
    """
    profile = db.scalar(select(Profile).where(Profile.user_id == current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning profile has not been created yet.",
        )
    return profile


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize student learning profile",
)
def create_student_profile(
    request: ProfileCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initializes a new learning profile for the authenticated student.
    Guarantees 1:1 relationship by rejecting duplicate creation attempts.
    """
    existing_profile = db.scalar(select(Profile).where(Profile.user_id == current_user.id))
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Learning profile already exists. Use PUT /profile to update your profile.",
        )

    new_profile = Profile(
        user_id=current_user.id,
        education_level=request.education_level.strip(),
        target_goal=request.target_goal.strip(),
        current_skill_level=request.current_skill_level.strip(),
        weekly_hours_available=request.weekly_hours_available,
        preferred_learning_style=request.preferred_learning_style.strip(),
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Update student learning profile",
)
def update_student_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates existing profile attributes (goals, hours, skill levels).
    Returns HTTP 404 if no profile exists to update.
    """
    profile = db.scalar(select(Profile).where(Profile.user_id == current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first using POST /profile.",
        )

    if request.education_level is not None:
        profile.education_level = request.education_level.strip()
    if request.target_goal is not None:
        profile.target_goal = request.target_goal.strip()
    if request.current_skill_level is not None:
        profile.current_skill_level = request.current_skill_level.strip()
    if request.weekly_hours_available is not None:
        profile.weekly_hours_available = request.weekly_hours_available
    if request.preferred_learning_style is not None:
        profile.preferred_learning_style = request.preferred_learning_style.strip()

    db.commit()
    db.refresh(profile)

    return profile
