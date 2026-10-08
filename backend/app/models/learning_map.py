"""
Learning Map Database Model.

Defines the roadmap container representing a student's chosen career or learning goal.
Contains ordered topics and manages active roadmap state.
"""

import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.topic import Topic


class LearningMap(Base):
    __tablename__ = "learning_maps"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the learning map (UUIDv4)",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key pointing to the owning student",
    )
    goal_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Career or subject goal, e.g., 'Java Backend Developer'",
    )
    learning_level: Mapped[str] = mapped_column(
        String(50),
        default="beginner",
        nullable=False,
        doc="The skill level of this roadmap: beginner, intermediate, or advanced",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Overview of what this learning journey covers",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Flag indicating whether this is the student's currently active roadmap",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of roadmap creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of last roadmap update",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="learning_maps",
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic",
        back_populates="learning_map",
        cascade="all, delete-orphan",
        order_by="Topic.sequence_order",
    )

    def __repr__(self) -> str:
        return f"<LearningMap id={self.id} goal={self.goal_title} user_id={self.user_id}>"
