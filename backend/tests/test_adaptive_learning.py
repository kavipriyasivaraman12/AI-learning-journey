"""
Adaptive Learning and Topic Progression Tests.

Tests:
1. High score (>= passing threshold) marks current topic COMPLETED and unlocks next topic.
2. High score returns PROCEED_TO_NEXT_TOPIC adaptive recommendation with explainable reason.
3. Low score (< passing threshold) keeps next topic LOCKED and returns REVIEW_AND_RETAKE recommendation.
4. Weak areas provide targeted conceptual study guidance.
5. Locked topic cannot be accessed or skipped before passing prerequisite assessment.
6. Multi-attempt scenario: failing attempt keeps topic locked; subsequent passing attempt unlocks next topic.
7. Standalone GET /topics/{topic_id}/adaptive-recommendation endpoint.
8. Unauthorized user cannot query adaptive recommendations for another student's topic.
"""

import pytest
from fastapi.testclient import TestClient


def test_high_score_adaptive_progression_and_unlocking(client: TestClient):
    """Passing an assessment automatically marks current topic COMPLETED and unlocks next topic."""
    # 1. Register & login
    client.post("/auth/register", json={"email": "adapt_pass@example.com", "password": "Password123!", "full_name": "Pass Student"})
    login_res = client.post("/auth/login", json={"email": "adapt_pass@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Setup profile & map
    client.post(
        "/profile",
        json={"education_level": "undergraduate", "target_goal": "Python Developer", "current_skill_level": "beginner", "weekly_hours_available": 10, "preferred_learning_style": "hands-on"},
        headers=headers,
    )
    map_res = client.post("/learning-maps", json={"goal_title": "Python Developer", "force_regenerate": False}, headers=headers)
    topics = map_res.json()["topics"]
    topic_1_id = topics[0]["id"]
    topic_2_id = topics[1]["id"]

    # Verify Topic 2 starts LOCKED
    assert topics[1]["progress"]["status"] == "LOCKED"

    # 3. Get assessment and submit passing answers (100%)
    quiz_res = client.get(f"/topics/{topic_1_id}/assessment", headers=headers)
    quiz = quiz_res.json()
    correct_indices = [0, 1, 2, 0, 1, 2, 1, 0, 0, 1, 0, 1, 0, 0, 0]
    answers = [
        {"question_id": q["id"], "selected_option_index": correct_indices[i % len(correct_indices)]}
        for i, q in enumerate(quiz["questions"])
    ]

    submit_res = client.post(f"/assessments/{quiz['id']}/submit", json={"answers": answers}, headers=headers)
    assert submit_res.status_code == 200
    report = submit_res.json()

    assert report["passed"] is True
    assert report["score_percentage"] == 100

    # 4. Verify adaptive recommendation
    rec = report["adaptive_recommendation"]
    assert rec is not None
    assert rec["action"] == "PROCEED_TO_NEXT_TOPIC"
    assert rec["next_topic_id"] == topic_2_id
    assert "unlocked" in rec["reason"].lower()

    # 5. Verify Topic 1 is COMPLETED and Topic 2 is now unlocked (NOT_STARTED)
    map_updated = client.get("/learning-maps/active", headers=headers).json()
    updated_topics = map_updated["topics"]
    assert updated_topics[0]["progress"]["status"] == "COMPLETED"
    assert updated_topics[1]["progress"]["status"] == "NOT_STARTED"


def test_low_score_keeps_next_topic_locked_with_targeted_weak_areas(client: TestClient):
    """Failing an assessment keeps next topic LOCKED and provides targeted weak area review guidance."""
    client.post("/auth/register", json={"email": "adapt_fail@example.com", "password": "Password123!", "full_name": "Fail Student"})
    login_res = client.post("/auth/login", json={"email": "adapt_fail@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={"education_level": "undergraduate", "target_goal": "Python Developer", "current_skill_level": "beginner", "weekly_hours_available": 10, "preferred_learning_style": "hands-on"},
        headers=headers,
    )
    map_res = client.post("/learning-maps", json={"goal_title": "Python Developer", "force_regenerate": False}, headers=headers)
    topics = map_res.json()["topics"]
    topic_1_id = topics[0]["id"]
    topic_2_id = topics[1]["id"]

    quiz_res = client.get(f"/topics/{topic_1_id}/assessment", headers=headers)
    quiz = quiz_res.json()

    # Submit failing answers (0%)
    answers = [
        {"question_id": quiz["questions"][0]["id"], "selected_option_index": 3},
        {"question_id": quiz["questions"][1]["id"], "selected_option_index": 3},
        {"question_id": quiz["questions"][2]["id"], "selected_option_index": 0},
    ]

    submit_res = client.post(f"/assessments/{quiz['id']}/submit", json={"answers": answers}, headers=headers)
    assert submit_res.status_code == 200
    report = submit_res.json()

    assert report["passed"] is False
    assert report["score_percentage"] == 0

    # Verify adaptive recommendation
    rec = report["adaptive_recommendation"]
    assert rec is not None
    assert rec["action"] == "REVIEW_AND_RETAKE"
    assert rec["next_topic_id"] is None
    assert "locked" in rec["reason"].lower()
    assert len(rec["weak_areas_guidance"]) > 0

    # Each weak area must have actionable advice
    for wag in rec["weak_areas_guidance"]:
        assert "concept_name" in wag
        assert "recommendation" in wag
        assert len(wag["recommendation"]) > 10

    # Verify Topic 2 remains LOCKED
    map_updated = client.get("/learning-maps/active", headers=headers).json()
    assert map_updated["topics"][1]["progress"]["status"] == "LOCKED"

    # Attempting to access Topic 2 content or assessment returns 403
    content_res = client.get(f"/topics/{topic_2_id}/content", headers=headers)
    assert content_res.status_code == 403


def test_retake_after_failure_unlocks_next_topic(client: TestClient):
    """Student fails on attempt 1 (next topic locked), then retakes and passes on attempt 2 (next topic unlocks)."""
    client.post("/auth/register", json={"email": "retake_student@example.com", "password": "Password123!", "full_name": "Retake Student"})
    login_res = client.post("/auth/login", json={"email": "retake_student@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={"education_level": "undergraduate", "target_goal": "Python Developer", "current_skill_level": "beginner", "weekly_hours_available": 10, "preferred_learning_style": "hands-on"},
        headers=headers,
    )
    map_res = client.post("/learning-maps", json={"goal_title": "Python Developer", "force_regenerate": False}, headers=headers)
    topics = map_res.json()["topics"]
    topic_1_id = topics[0]["id"]
    topic_2_id = topics[1]["id"]

    quiz_res = client.get(f"/topics/{topic_1_id}/assessment", headers=headers)
    quiz = quiz_res.json()

    # Attempt 1: Failed
    client.post(
        f"/assessments/{quiz['id']}/submit",
        json={"answers": [{"question_id": q["id"], "selected_option_index": 3} for q in quiz["questions"]]},
        headers=headers,
    )
    # Check locked
    assert client.get(f"/topics/{topic_2_id}/content", headers=headers).status_code == 403

    # Attempt 2: Passed with 100%
    correct_indices = [0, 1, 2, 0, 1, 2, 1, 0, 0, 1, 0, 1, 0, 0, 0]
    pass_res = client.post(
        f"/assessments/{quiz['id']}/submit",
        json={
            "answers": [
                {"question_id": q["id"], "selected_option_index": correct_indices[i % len(correct_indices)]}
                for i, q in enumerate(quiz["questions"])
            ]
        },
        headers=headers,
    )
    assert pass_res.json()["passed"] is True
    assert pass_res.json()["adaptive_recommendation"]["action"] == "PROCEED_TO_NEXT_TOPIC"

    # Check now unlocked and accessible
    content_res = client.get(f"/topics/{topic_2_id}/content", headers=headers)
    assert content_res.status_code == 200


def test_standalone_adaptive_recommendation_endpoint(client: TestClient):
    """GET /topics/{topic_id}/adaptive-recommendation returns the accurate recommendation."""
    client.post("/auth/register", json={"email": "standalone_rec@example.com", "password": "Password123!", "full_name": "Rec Tester"})
    login_res = client.post("/auth/login", json={"email": "standalone_rec@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={"education_level": "undergraduate", "target_goal": "Python Developer", "current_skill_level": "beginner", "weekly_hours_available": 10, "preferred_learning_style": "hands-on"},
        headers=headers,
    )
    map_res = client.post("/learning-maps", json={"goal_title": "Python Developer", "force_regenerate": False}, headers=headers)
    topic_1_id = map_res.json()["topics"][0]["id"]

    # Generate assessment
    client.get(f"/topics/{topic_1_id}/assessment", headers=headers)

    # Query adaptive recommendation before quiz submission
    rec_pre = client.get(f"/topics/{topic_1_id}/adaptive-recommendation", headers=headers)
    assert rec_pre.status_code == 200
    assert rec_pre.json()["action"] == "TAKE_ASSESSMENT"


def test_unauthorized_adaptive_recommendation_access(client: TestClient):
    """Student B cannot query adaptive recommendation for Student A's topic."""
    # Student A
    client.post("/auth/register", json={"email": "student_orig@example.com", "password": "Password123!", "full_name": "Original Student"})
    login_a = client.post("/auth/login", json={"email": "student_orig@example.com", "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/profile", json={"education_level": "undergraduate", "target_goal": "Python Developer", "current_skill_level": "beginner", "weekly_hours_available": 10, "preferred_learning_style": "hands-on"}, headers=headers_a)
    map_a = client.post("/learning-maps", json={"goal_title": "Python Developer", "force_regenerate": False}, headers=headers_a)
    topic_a_id = map_a.json()["topics"][0]["id"]
    client.get(f"/topics/{topic_a_id}/assessment", headers=headers_a)

    # Student B
    client.post("/auth/register", json={"email": "student_intruder@example.com", "password": "Password123!", "full_name": "Intruder"})
    login_b = client.post("/auth/login", json={"email": "student_intruder@example.com", "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Student B attempts to access Student A's topic adaptive recommendation
    rec_res = client.get(f"/topics/{topic_a_id}/adaptive-recommendation", headers=headers_b)
    assert rec_res.status_code == 404
