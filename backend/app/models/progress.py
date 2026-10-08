"""
Topic Progress Database Model.

Tracks each student's progress and mastery state for individual topics.
Supports statuses: LOCKED, NOT_STARTED, IN_PROGRESS, and COMPLETED.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.topic import Topic


class TopicProgress(Base):
    __tablename__ = "topic_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic_progress"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the progress record (UUIDv4)",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the student",
    )
    topic_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the topic being tracked",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="LOCKED",
        doc="Status: LOCKED, NOT_STARTED, IN_PROGRESS, COMPLETED",
    )
    mastery_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Latest assessment or mastery score percentage (0-100)",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when topic was successfully completed",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="topic_progresses",
    )
    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="progress_records",
    )

    def __repr__(self) -> str:
        return f"<TopicProgress user={self.user_id} topic={self.topic_id} status={self.status} score={self.mastery_score}>"
