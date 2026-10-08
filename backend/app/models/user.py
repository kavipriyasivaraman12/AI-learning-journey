"""
User Database Model.

Defines the SQLAlchemy 2.x ORM model for application users.
Uses UUID primary keys and stores only bcrypt-hashed passwords.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.learning_map import LearningMap
    from app.models.progress import TopicProgress
    from app.models.assessment import AssessmentAttempt


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the user (UUIDv4 string)",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User email address used for login",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt-hashed password (never store plaintext)",
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Student full name",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Flag indicating if the user account is active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of account creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of last update",
    )

    # 1:1 relationship with Profile
    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1:N relationship with Learning Maps
    learning_maps: Mapped[List["LearningMap"]] = relationship(
        "LearningMap",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 1:N relationship with Topic Progress tracking
    topic_progresses: Mapped[List["TopicProgress"]] = relationship(
        "TopicProgress",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 1:N relationship with Assessment Attempts
    assessment_attempts: Mapped[List["AssessmentAttempt"]] = relationship(
        "AssessmentAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
