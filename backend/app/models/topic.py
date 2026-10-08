"""
Topic and TopicContent Database Models.

Defines ordered learning units (Topic) and their associated persistent educational
materials (TopicContent) such as summaries, deep explanations, code examples, and key takeaways.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.learning_map import LearningMap
    from app.models.progress import TopicProgress
    from app.models.assessment import Assessment


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("learning_map_id", "sequence_order", name="uq_topic_map_sequence"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the topic (UUIDv4)",
    )
    learning_map_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("learning_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the parent learning roadmap",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Title of the topic (e.g. 'Object-Oriented Programming Fundamentals')",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Short description of what the student will master",
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Prerequisite order in the roadmap (1, 2, 3...)",
    )
    difficulty: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Beginner",
        doc="Difficulty rating: Beginner, Intermediate, Advanced",
    )
    estimated_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=45,
        doc="Estimated study time in minutes",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    learning_map: Mapped["LearningMap"] = relationship(
        "LearningMap",
        back_populates="topics",
    )
    content: Mapped[Optional["TopicContent"]] = relationship(
        "TopicContent",
        back_populates="topic",
        uselist=False,
        cascade="all, delete-orphan",
    )
    assessment: Mapped[Optional["Assessment"]] = relationship(
        "Assessment",
        back_populates="topic",
        uselist=False,
        cascade="all, delete-orphan",
    )
    progress_records: Mapped[List["TopicProgress"]] = relationship(
        "TopicProgress",
        back_populates="topic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Topic id={self.id} order={self.sequence_order} title={self.title}>"


class TopicContent(Base):
    __tablename__ = "topic_contents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the topic content (UUIDv4)",
    )
    topic_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("topics.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign key to the topic (1:1 relation)",
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="High-level conceptual overview",
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="In-depth conceptual breakdown with real-world analogies",
    )
    code_examples: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Annotated syntax and working code snippets",
    )
    common_mistakes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Pitfalls, anti-patterns, and debugging tips",
    )
    key_takeaways: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Summary bullet points for quick revision",
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="content",
    )

    def __repr__(self) -> str:
        return f"<TopicContent id={self.id} topic_id={self.topic_id}>"
