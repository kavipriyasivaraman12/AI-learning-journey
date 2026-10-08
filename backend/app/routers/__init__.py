"""
Routers Package.

Exports FastAPI API routers.
"""

from app.routers.auth_router import router as auth_router
from app.routers.profile_router import router as profile_router
from app.routers.map_router import router as map_router
from app.routers.topic_router import router as topic_router
from app.routers.progress_router import router as progress_router
from app.routers.assessment_router import router as assessment_router
from app.routers.tutor_router import router as tutor_router

__all__ = [
    "auth_router",
    "profile_router",
    "map_router",
    "topic_router",
    "progress_router",
    "assessment_router",
    "tutor_router",
]


