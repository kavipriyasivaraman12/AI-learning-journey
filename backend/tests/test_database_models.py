"""
Unit Tests for Database Models and Relationships.

Validates SQLAlchemy 2.x ORM models, primary/foreign keys, 1:1 constraints,
cascade deletions, and JSON column persistence.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import (
    User,
    Profile,
    LearningMap,
    Topic,
    TopicContent,
    TopicProgress,
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
)


@pytest.fixture
def test_user(db_session):
    """Creates and returns a persisted test User entity."""
    user = User(
        email="db_tester@example.com",
        hashed_password="hashed_sample_password",
        full_name="DB Tester",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_learning_map_with_topics(db_session, test_user):
    """Verify creating a LearningMap with ordered Topics and bidirectional relationships."""
    lmap = LearningMap(
        user_id=test_user.id,
        goal_title="Java Backend Developer",
        description="Complete roadmap for Java Backend mastery",
        is_active=True,
    )
    db_session.add(lmap)
    db_session.commit()
    db_session.refresh(lmap)

    topic1 = Topic(
        learning_map_id=lmap.id,
        title="Object Oriented Programming",
        sequence_order=1,
        difficulty="Beginner",
        estimated_minutes=60,
    )
    topic2 = Topic(
        learning_map_id=lmap.id,
        title="Java Collections Framework",
        sequence_order=2,
        difficulty="Intermediate",
        estimated_minutes=90,
    )
    db_session.add_all([topic1, topic2])
    db_session.commit()

    # Re-query
    retrieved_map = db_session.scalar(select(LearningMap).where(LearningMap.id == lmap.id))
    assert retrieved_map is not None
    assert len(retrieved_map.topics) == 2
    assert retrieved_map.topics[0].title == "Object Oriented Programming"
    assert retrieved_map.topics[1].title == "Java Collections Framework"


def test_topic_unique_sequence_constraint(db_session, test_user):
    """Verify that duplicate sequence_order on the same LearningMap raises IntegrityError."""
    lmap = LearningMap(user_id=test_user.id, goal_title="Web Dev")
    db_session.add(lmap)
    db_session.commit()
    db_session.refresh(lmap)

    t1 = Topic(learning_map_id=lmap.id, title="Topic 1", sequence_order=1)
    t2 = Topic(learning_map_id=lmap.id, title="Topic 2 Duplicate Order", sequence_order=1)
    db_session.add(t1)
    db_session.commit()

    db_session.add(t2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_topic_content_1_to_1_attachment(db_session, test_user):
    """Verify TopicContent 1:1 relationship with Topic."""
    lmap = LearningMap(user_id=test_user.id, goal_title="Python Track")
    db_session.add(lmap)
    db_session.commit()
    db_session.refresh(lmap)

    topic = Topic(learning_map_id=lmap.id, title="Variables & Types", sequence_order=1)
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    content = TopicContent(
        topic_id=topic.id,
        summary="Overview of variables in Python",
        explanation="Variables are pointers to objects in memory.",
        code_examples="x = 10\nname = 'Alice'",
        common_mistakes="Confusing assignment (=) with equality (==).",
        key_takeaways="Python is dynamically typed.",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(topic)

    assert topic.content is not None
    assert topic.content.summary == "Overview of variables in Python"
    assert "name = 'Alice'" in topic.content.code_examples


def test_topic_progress_lifecycle(db_session, test_user):
    """Verify TopicProgress status changes and constraints."""
    lmap = LearningMap(user_id=test_user.id, goal_title="FastAPI Track")
    db_session.add(lmap)
    db_session.commit()
    db_session.refresh(lmap)

    topic = Topic(learning_map_id=lmap.id, title="Routers", sequence_order=1)
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    progress = TopicProgress(
        user_id=test_user.id,
        topic_id=topic.id,
        status="IN_PROGRESS",
        mastery_score=85,
    )
    db_session.add(progress)
    db_session.commit()
    db_session.refresh(progress)

    assert progress.status == "IN_PROGRESS"
    assert progress.mastery_score == 85

    # Test duplicate progress rejection for same user + topic
    dup_progress = TopicProgress(user_id=test_user.id, topic_id=topic.id, status="COMPLETED")
    db_session.add(dup_progress)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_assessment_and_attempt_with_json_data(db_session, test_user):
    """Verify Assessment, questions, and attempt logging with JSON weak areas."""
    lmap = LearningMap(user_id=test_user.id, goal_title="DB Track")
    db_session.add(lmap)
    db_session.commit()
    db_session.refresh(lmap)

    topic = Topic(learning_map_id=lmap.id, title="SQL Indexing", sequence_order=1)
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    assessment = Assessment(
        topic_id=topic.id,
        title="SQL Indexing Mastery Quiz",
        passing_score_percentage=75,
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)

    q1 = AssessmentQuestion(
        assessment_id=assessment.id,
        question_text="Which index type is best for equality lookups?",
        options=["B-Tree", "Hash", "GIN", "BRIN"],
        correct_option_index=1,
        explanation="Hash indexes have O(1) lookups for equality.",
    )
    db_session.add(q1)
    db_session.commit()

    attempt = AssessmentAttempt(
        user_id=test_user.id,
        assessment_id=assessment.id,
        score_percentage=80,
        passed=True,
        weak_areas=["BRIN indexing", "Clustered indexes"],
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    assert attempt.passed is True
    assert "BRIN indexing" in attempt.weak_areas
    assert len(assessment.questions) == 1


def test_cascade_delete_learning_map(db_session, test_user):
    """Verify that deleting a LearningMap automatically deletes all child topics and content."""
    lmap = LearningMap(user_id=test_user.id, goal_title="To Be Deleted")
    db_session.add(lmap)
    db_session.commit()
    db_session.refresh(lmap)

    topic = Topic(learning_map_id=lmap.id, title="Child Topic", sequence_order=1)
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    content = TopicContent(
        topic_id=topic.id,
        summary="Summary",
        explanation="Explanation",
    )
    db_session.add(content)
    db_session.commit()

    topic_id = topic.id
    content_id = content.id

    # Delete the learning map
    db_session.delete(lmap)
    db_session.commit()

    # Verify children are deleted
    assert db_session.scalar(select(Topic).where(Topic.id == topic_id)) is None
    assert db_session.scalar(select(TopicContent).where(TopicContent.id == content_id)) is None
