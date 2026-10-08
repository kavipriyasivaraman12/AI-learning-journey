"""
Main Application Entry Point.

Initializes the FastAPI application, registers middleware (CORS),
includes API routers (Auth, Profile, Learning Maps, Topics, Progress),
and sets up diagnostic endpoints.
"""

from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, check_database_connection, init_db_schema
from app.routers.auth_router import router as auth_router
from app.routers.profile_router import router as profile_router
from app.routers.map_router import router as map_router
from app.routers.topic_router import router as topic_router
from app.routers.progress_router import router as progress_router
from app.routers.assessment_router import router as assessment_router
from app.routers.tutor_router import router as tutor_router


# Import all models so Base.metadata knows about them
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes tables and performs safe non-destructive schema synchronization.
    """
    try:
        init_db_schema()
    except Exception as e:
        # If database is offline at startup, don't crash; log for diagnostics
        print(f"[Lifespan Notice] Database initialization notice: {e}")
    yield


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Academic Mini-Project: Backend API for Personalized Learning Journey Generator.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(map_router)
app.include_router(topic_router)
app.include_router(progress_router)
app.include_router(assessment_router)
app.include_router(tutor_router)




@app.get("/", tags=["General"])
def root():
    """Root endpoint providing basic API info."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Monitoring"])
def health_check():
    """
    Health check and diagnostics endpoint.
    Checks server status and reports database connectivity.
    """
    db_status = check_database_connection()
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
    }
