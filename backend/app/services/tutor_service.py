"""
AI Topic Tutor Service Layer.

Handles scoped student queries on specific topics, enforces prerequisite access checks,
injects learner profile context, and delegates to the AIService for pedagogical explanations.
"""

from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.topic import Topic, TopicContent
from app.models.profile import Profile
from app.models.progress import TopicProgress
from app.schemas.tutor_schema import TopicTutorResponse
from app.services.ai_service import ai_service


def ask_topic_tutor_service(
    db: Session,
    user_id: str,
    topic_id: str,
    question: str,
    conversation_history: Optional[List[Any]] = None,
) -> TopicTutorResponse:
    """
    Provides interactive AI tutoring scoped to the specified topic:
    1. Enforces student ownership and prerequisite unlock status.
    2. Retrieves student's skill level from their profile.
    3. Requests a personalized explanation, code snippet, common pitfall, and practice question.
    """
    topic = db.scalar(select(Topic).where(Topic.id == topic_id))
    if not topic or topic.learning_map.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )

    # Check topic progression lock
    progress = db.scalar(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic.id,
        )
    )
    if progress and progress.status == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access AI tutor for a locked topic. Please unlock prerequisite topics first.",
        )

    # Retrieve student skill level and goal
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    student_level = profile.current_skill_level if profile else "beginner"
    goal_title = topic.learning_map.goal_title

    # Retrieve or generate actual topic content for complete grounding
    content = db.scalar(select(TopicContent).where(TopicContent.topic_id == topic.id))
    if not content:
        try:
            profile_context = {
                "current_skill_level": student_level,
                "preferred_learning_style": profile.preferred_learning_style if profile else "hands-on",
            }
            ai_content = ai_service.generate_topic_content(
                topic_title=topic.title,
                goal_title=goal_title,
                profile_context=profile_context,
            )
            content = TopicContent(
                topic_id=topic.id,
                summary=ai_content.summary,
                explanation=ai_content.explanation,
                code_examples=ai_content.code_examples,
                common_mistakes=ai_content.common_mistakes,
                key_takeaways=ai_content.key_takeaways,
            )
            db.add(content)
            db.commit()
            db.refresh(content)
        except Exception:
            content = None

    topic_content_data = None
    if content:
        topic_content_data = {
            "summary": content.summary,
            "explanation": content.explanation,
            "code_examples": content.code_examples or "",
            "common_mistakes": content.common_mistakes or "",
            "key_takeaways": content.key_takeaways or "",
        }

    # Call AI Service layer with all 8 contextual items
    ai_response = ai_service.ask_topic_tutor(
        topic_title=topic.title,
        goal_title=goal_title,
        student_level=student_level,
        question=question,
        topic_description=topic.description or "",
        topic_difficulty=topic.difficulty or "Beginner",
        topic_content=topic_content_data,
        conversation_history=conversation_history,
    )

    return TopicTutorResponse(
        topic_id=topic.id,
        topic_title=topic.title,
        student_skill_level=student_level,
        question=question,
        explanation=ai_response.explanation,
        code_example=ai_response.code_example,
        common_mistake=ai_response.common_mistake,
        practice_question=ai_response.practice_question,
        is_topic_related=ai_response.is_topic_related,
    )
