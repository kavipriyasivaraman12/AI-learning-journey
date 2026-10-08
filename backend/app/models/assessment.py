"""
Assessment, Question, and Attempt Database Models.

Defines topic quizzes (Assessment), multiple-choice questions (AssessmentQuestion),
and student submission results (AssessmentAttempt) with weak area detection tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.topic import Topic


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the assessment (UUIDv4)",
    )
    topic_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("topics.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign key to the topic evaluated (1:1 relation)",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Assessment title (e.g., 'OOP Concepts Mastery Quiz')",
    )
    passing_score_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
        doc="Passing grade threshold required to unlock next topic (e.g. 70%)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="assessment",
    )
    questions: Mapped[List["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )
    attempts: Mapped[List["AssessmentAttempt"]] = relationship(
        "AssessmentAttempt",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} topic_id={self.topic_id} title={self.title}>"


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the question (UUIDv4)",
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to parent assessment",
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Question prompt text",
    )
    options: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        doc="List of answer choices, e.g. ['Choice A', 'Choice B', 'Choice C', 'Choice D']",
    )
    correct_option_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="0-indexed position of the correct answer",
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Explanation of why the correct answer is right",
    )
    concept_tag: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
        doc="Specific concept or sub-skill being tested, e.g. 'List Indexing'",
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="questions",
    )

    def __repr__(self) -> str:
        return f"<AssessmentQuestion id={self.id} assessment_id={self.assessment_id}>"


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        doc="Unique identifier for the attempt log (UUIDv4)",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the student who took the quiz",
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the assessment attempted",
    )
    score_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Calculated score (0 - 100%)",
    )
    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="Flag whether student met or exceeded the passing threshold",
    )
    weak_areas: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of sub-concepts or topics where student made mistakes",
    )
    used_question_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of question IDs used in this attempt (for retake randomization)",
    )
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="assessment_attempts",
    )
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="attempts",
    )

    def __repr__(self) -> str:
        return f"<AssessmentAttempt id={self.id} user={self.user_id} score={self.score_percentage}% passed={self.passed}>"
