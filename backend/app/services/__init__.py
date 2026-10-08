"""
Services Package.

Exports business logic, progress, and AI services.
"""

from app.services.ai_service import (
    AIService,
    AIRoadmapTopic,
    AIRoadmapResponse,
    AITopicContentResponse,
    ai_service,
)
from app.services.learning_service import (
    get_or_create_learning_map,
    build_learning_map_response,
)
from app.services.progress_service import (
    complete_topic_and_unlock_next,
    calculate_dashboard_analytics,
)
from app.services.assessment_service import (
    get_or_create_topic_assessment,
    evaluate_assessment_submission,
)
from app.services.adaptive_service import (
    generate_adaptive_recommendation,
)
from app.services.tutor_service import (
    ask_topic_tutor_service,
)

__all__ = [
    "AIService",
    "AIRoadmapTopic",
    "AIRoadmapResponse",
    "AITopicContentResponse",
    "ai_service",
    "get_or_create_learning_map",
    "build_learning_map_response",
    "complete_topic_and_unlock_next",
    "calculate_dashboard_analytics",
    "get_or_create_topic_assessment",
    "evaluate_assessment_submission",
    "generate_adaptive_recommendation",
    "ask_topic_tutor_service",
]



