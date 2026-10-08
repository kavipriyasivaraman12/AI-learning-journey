"""
Learning Profile Database Model.

Defines the SQLAlchemy 2.x ORM model for a student's learning profile.
Maintains a strict 1:1 foreign key relationship with the User model.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the profile (UUIDv4)",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign key pointing to the user who owns this profile",
    )
    education_level: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="e.g., Undergraduate, Graduate, High School, Working Professional",
    )
    target_goal: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="e.g., Java Backend Developer, Full Stack Developer, Data Scientist",
    )
    current_skill_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Self-reported baseline skill level: Beginner, Intermediate, Advanced",
    )
    weekly_hours_available: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        doc="Hours per week the student can dedicate to learning",
    )
    preferred_learning_style: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Practical",
        doc="e.g., Practical / Project-based, Theoretical, Visual / Conceptual",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when profile was initialized",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of last profile update",
    )

    # 1:1 relationship with User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} user_id={self.user_id} goal={self.target_goal}>"
