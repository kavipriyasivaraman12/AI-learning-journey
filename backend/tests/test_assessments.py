"""
Assessment and Quiz System Tests.

Tests:
1. Assessment generation for a topic (cache miss).
2. Assessment caching / reuse (does not duplicate or re-generate).
3. Student-facing question retrieval (correct answers hidden).
4. Answer submission with 100% score (all correct).
5. Answer submission with imperfect score and weak-area detection.
6. Assessment attempt history logging.
7. Unauthorized access to locked topic assessment (403).
8. Unauthorized access to another student's topic/assessment (404).
9. Invalid / nonexistent assessment submission handling (404).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.services.ai_service import ai_service, AIAssessmentResponse, AIAssessmentQuestion


def test_get_or_create_assessment_generation(client: TestClient):
    """Test generating a new assessment quiz for an unlocked topic."""
    # 1. Register & login
    client.post(
        "/auth/register",
        json={"email": "quizuser1@example.com", "password": "Password123!", "full_name": "Quiz Student"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "quizuser1@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create profile & learning map
    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    first_topic = map_res.json()["topics"][0]
    topic_id = first_topic["id"]

    # 3. Request assessment
    response = client.get(f"/topics/{topic_id}/assessment", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["topic_id"] == topic_id
    assert "id" in data
    assert "title" in data
    assert data["passing_score_percentage"] == 70
    assert len(data["questions"]) >= 2

    # Verify correct answers and explanations are NOT exposed in student view
    for q in data["questions"]:
        assert "id" in q
        assert "question_text" in q
        assert "options" in q
        assert len(q["options"]) >= 2
        assert "correct_option_index" not in q
        assert "explanation" not in q


def test_assessment_caching_and_reuse(client: TestClient):
    """Verify that requesting an assessment twice returns the same cached assessment."""
    client.post(
        "/auth/register",
        json={"email": "quizcache@example.com", "password": "Password123!", "full_name": "Cache Tester"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "quizcache@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    topic_id = map_res.json()["topics"][0]["id"]

    # First call: generates and caches
    res1 = client.get(f"/topics/{topic_id}/assessment", headers=headers)
    assert res1.status_code == 200
    assessment_id_1 = res1.json()["id"]

    # Second call: must return exact same assessment ID
    res2 = client.get(f"/topics/{topic_id}/assessment", headers=headers)
    assert res2.status_code == 200
    assessment_id_2 = res2.json()["id"]

    assert assessment_id_1 == assessment_id_2


def test_submit_assessment_perfect_score(client: TestClient):
    """Test submitting an assessment where all answers are correct (100% score, passed, no weak areas)."""
    client.post(
        "/auth/register",
        json={"email": "perfect@example.com", "password": "Password123!", "full_name": "Perfect Student"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "perfect@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    topic_id = map_res.json()["topics"][0]["id"]

    quiz_res = client.get(f"/topics/{topic_id}/assessment", headers=headers)
    quiz = quiz_res.json()
    assessment_id = quiz["id"]

    # Fallback assessment has 15 questions with deterministic correct options
    correct_indices = [0, 1, 2, 0, 1, 2, 1, 0, 0, 1, 0, 1, 0, 0, 0]
    answers = [
        {"question_id": q["id"], "selected_option_index": correct_indices[i % len(correct_indices)]}
        for i, q in enumerate(quiz["questions"])
    ]

    submit_res = client.post(
        f"/assessments/{assessment_id}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert submit_res.status_code == 200
    report = submit_res.json()

    assert report["assessment_id"] == assessment_id
    assert report["score_percentage"] == 100
    assert report["passed"] is True
    assert report["correct_answers_count"] == len(quiz["questions"])
    assert report["total_questions"] == len(quiz["questions"])
    assert len(report["weak_areas"]) == 0
    assert len(report["question_results"]) == len(quiz["questions"])
    assert all(qr["is_correct"] is True for qr in report["question_results"])


def test_submit_assessment_with_weak_areas(client: TestClient):
    """Test submitting incorrect answers triggers weak-area identification and failure below passing threshold."""
    client.post(
        "/auth/register",
        json={"email": "student_fail@example.com", "password": "Password123!", "full_name": "Needs Practice"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "student_fail@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    topic_id = map_res.json()["topics"][0]["id"]

    quiz_res = client.get(f"/topics/{topic_id}/assessment", headers=headers)
    quiz = quiz_res.json()
    assessment_id = quiz["id"]

    # Choose wrong answers for all questions
    answers = [
        {"question_id": quiz["questions"][0]["id"], "selected_option_index": 3},  # Correct is 0
        {"question_id": quiz["questions"][1]["id"], "selected_option_index": 3},  # Correct is 1
        {"question_id": quiz["questions"][2]["id"], "selected_option_index": 0},  # Correct is 2
    ]

    submit_res = client.post(
        f"/assessments/{assessment_id}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert submit_res.status_code == 200
    report = submit_res.json()

    assert report["score_percentage"] == 0
    assert report["passed"] is False
    assert report["correct_answers_count"] == 0
    assert len(report["weak_areas"]) > 0


def test_assessment_attempt_history(client: TestClient):
    """Test that multiple assessment attempts are recorded in history."""
    client.post(
        "/auth/register",
        json={"email": "history_user@example.com", "password": "Password123!", "full_name": "History Student"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "history_user@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    topic_id = map_res.json()["topics"][0]["id"]

    quiz_res = client.get(f"/topics/{topic_id}/assessment", headers=headers)
    quiz = quiz_res.json()
    assessment_id = quiz["id"]

    # First attempt: all wrong
    client.post(
        f"/assessments/{assessment_id}/submit",
        json={"answers": [{"question_id": q["id"], "selected_option_index": 3} for q in quiz["questions"]]},
        headers=headers,
    )

    # Second attempt: all correct
    correct_indices = [0, 1, 2, 0, 1, 2, 1, 0, 0, 1, 0, 1, 0, 0, 0]
    client.post(
        f"/assessments/{assessment_id}/submit",
        json={
            "answers": [
                {"question_id": q["id"], "selected_option_index": correct_indices[i % len(correct_indices)]}
                for i, q in enumerate(quiz["questions"])
            ]
        },
        headers=headers,
    )

    # Fetch attempts
    history_res = client.get(f"/assessments/{assessment_id}/attempts", headers=headers)
    assert history_res.status_code == 200
    attempts = history_res.json()

    assert len(attempts) == 2
    assert attempts[0]["score_percentage"] == 100  # Most recent first
    assert attempts[1]["score_percentage"] == 0


def test_locked_topic_assessment_forbidden(client: TestClient):
    """Test that accessing assessment for a LOCKED topic returns HTTP 403."""
    client.post(
        "/auth/register",
        json={"email": "locked_quiz@example.com", "password": "Password123!", "full_name": "Locked Quiz User"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "locked_quiz@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    # Topic 2 is LOCKED initially
    locked_topic_id = map_res.json()["topics"][1]["id"]

    response = client.get(f"/topics/{locked_topic_id}/assessment", headers=headers)
    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()


def test_unauthorized_assessment_access(client: TestClient):
    """Test that user B cannot access or submit quiz for user A's topic."""
    # User A
    client.post(
        "/auth/register",
        json={"email": "student_a@example.com", "password": "Password123!", "full_name": "Student A"},
    )
    login_a = client.post("/auth/login", json={"email": "student_a@example.com", "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post(
        "/profile",
        json={"education_level": "undergraduate", "target_goal": "Python Developer", "current_skill_level": "beginner", "weekly_hours_available": 10, "preferred_learning_style": "hands-on"},
        headers=headers_a,
    )
    map_a = client.post("/learning-maps", json={"goal_title": "Python Developer", "force_regenerate": False}, headers=headers_a)
    topic_a_id = map_a.json()["topics"][0]["id"]
    quiz_a = client.get(f"/topics/{topic_a_id}/assessment", headers=headers_a).json()


    # User B
    client.post(
        "/auth/register",
        json={"email": "student_b@example.com", "password": "Password123!", "full_name": "Student B"},
    )
    login_b = client.post("/auth/login", json={"email": "student_b@example.com", "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B tries to access User A's topic assessment
    get_res = client.get(f"/topics/{topic_a_id}/assessment", headers=headers_b)
    assert get_res.status_code == 404

    # User B tries to submit to User A's assessment
    submit_res = client.post(
        f"/assessments/{quiz_a['id']}/submit",
        json={"answers": [{"question_id": quiz_a["questions"][0]["id"], "selected_option_index": 0}]},
        headers=headers_b,
    )
    assert submit_res.status_code == 404
