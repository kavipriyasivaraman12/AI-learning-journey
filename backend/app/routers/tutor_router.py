"""
AI Topic Tutor Router.

Provides interactive endpoints allowing students to ask conceptual, syntax,
and debugging questions specifically about the topic they are currently studying.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.security import get_current_user
from app.schemas.tutor_schema import TopicTutorRequest, TopicTutorResponse
from app.services.tutor_service import ask_topic_tutor_service

router = APIRouter(prefix="/topics", tags=["AI Topic Tutor"])


@router.post(
    "/{topic_id}/tutor",
    response_model=TopicTutorResponse,
    summary="Ask a question to the AI Topic Tutor",
)
def ask_topic_tutor_endpoint(
    topic_id: str,
    payload: TopicTutorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Topic-specific AI Tutor:
    1. Authenticates student and validates ownership of the topic.
    2. Enforces prerequisite unlock checks (rejects queries on locked topics with 403).
    3. Customizes explanation depth based on learner's skill level.
    4. Provides structured answers with code snippets, common pitfalls, and self-check questions.
    5. Politely redirects unrelated questions back to the current topic.
    """
    return ask_topic_tutor_service(
        db=db,
        user_id=current_user.id,
        topic_id=topic_id,
        question=payload.question,
        conversation_history=payload.conversation_history,
    )
