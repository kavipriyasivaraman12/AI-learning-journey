"""
Schemas Package.

Exports all Pydantic request and response schemas.
"""

from app.schemas.user_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    TokenPayload,
)
from app.schemas.profile_schema import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
)
from app.schemas.map_schema import (
    TopicProgressSummary,
    TopicSummaryResponse,
    LearningMapCreateRequest,
    LearningMapResponse,
    LearningMapListItem,
)
from app.schemas.topic_schema import (
    TopicContentResponse,
    TopicDetailResponse,
)
from app.schemas.progress_schema import (
    CurrentTopicSummary,
    DashboardAnalyticsResponse,
    TopicCompleteRequest,
)
from app.schemas.assessment_schema import (
    AssessmentQuestionStudentView,
    AssessmentResponse,
    AssessmentSubmitAnswer,
    AssessmentSubmitRequest,
    QuestionResult,
    AssessmentAttemptResponse,
    AssessmentAttemptHistoryItem,
)
from app.schemas.adaptive_schema import (
    WeakAreaGuidance,
    AdaptiveRecommendationResponse,
)
from app.schemas.tutor_schema import (
    TopicTutorRequest,
    TopicTutorResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "TokenPayload",
    "ProfileCreateRequest",
    "ProfileUpdateRequest",
    "ProfileResponse",
    "TopicProgressSummary",
    "TopicSummaryResponse",
    "LearningMapCreateRequest",
    "LearningMapResponse",
    "LearningMapListItem",
    "TopicContentResponse",
    "TopicDetailResponse",
    "CurrentTopicSummary",
    "DashboardAnalyticsResponse",
    "TopicCompleteRequest",
    "AssessmentQuestionStudentView",
    "AssessmentResponse",
    "AssessmentSubmitAnswer",
    "AssessmentSubmitRequest",
    "QuestionResult",
    "AssessmentAttemptResponse",
    "AssessmentAttemptHistoryItem",
    "WeakAreaGuidance",
    "AdaptiveRecommendationResponse",
    "TopicTutorRequest",
    "TopicTutorResponse",
]



