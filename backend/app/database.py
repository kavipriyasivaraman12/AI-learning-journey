"""
Database Connection and Session Management Module.

Configures SQLAlchemy ORM engine and session factory with psycopg v3 driver.
Provides FastAPI dependency for injecting transactional database sessions.
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Create SQLAlchemy engine using the psycopg (v3) URL
# connect_timeout=3 ensures the app does not hang if the DB is momentarily offline
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3},
)

# Session factory for handling requests
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to an endpoint.
    Ensures that sessions are properly closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db_schema() -> None:
    """
    Initializes database tables and performs safe, non-destructive schema synchronization.
    Safely adds missing columns without modifying existing data or dropping tables.
    """
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(
                    text(
                        "ALTER TABLE learning_maps ADD COLUMN IF NOT EXISTS learning_level VARCHAR(50) NOT NULL DEFAULT 'beginner'"
                    )
                )
    except Exception as e:
        pass
    try:
        with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(
                    text(
                        "ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS concept_tag VARCHAR(200) NOT NULL DEFAULT ''"
                    )
                )
    except Exception as e:
        pass
    try:
        with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(
                    text(
                        "ALTER TABLE assessment_attempts ADD COLUMN IF NOT EXISTS used_question_ids JSON NOT NULL DEFAULT '[]'"
                    )
                )
    except Exception as e:
        pass


def check_database_connection() -> dict:
    """
    Verifies if the PostgreSQL database is reachable.
    Used by the /health endpoint to report system diagnostics.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "connected", "database": "PostgreSQL"}
    except Exception as e:
        return {"status": "unreachable", "detail": "PostgreSQL server not running locally or credentials incorrect."}

