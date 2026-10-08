"""
End-to-End Complete User Journey Test.

Simulates the full student lifecycle:
1. Registration & Authentication
2. Learning Profile Setup
3. AI Personalized Learning Map Generation
4. Content Reading for Active Topic
5. Interactive Tutoring with AI Topic Tutor
6. Topic Assessment - Failure Attempt (verify next topic remains locked + weak areas guidance)
7. Topic Assessment - Passing Attempt (verify topic marked completed + next topic unlocked)
8. Progression to newly unlocked Topic 2
9. Dashboard Analytics Verification
"""

from unittest.mock import MagicMock
import json
import pytest
from fastapi.testclient import TestClient
from app.services.ai_service import ai_service


def test_complete_student_learning_lifecycle(client: TestClient, monkeypatch):
    mock_gemini = MagicMock()
    mock_res = MagicMock()
    mock_res.text = json.dumps({
        "explanation": "Variables in Python store references to values in memory. You can practice by creating variables of different types and inspecting their values with print().",
        "code_example": "x = 42\nname = 'Python'\nprint(f'{name}: {x}')",
        "common_mistake": "Using reserved keywords as variable names.",
        "practice_question": "What happens when you reassign a variable from an int to a string?",
        "is_topic_related": True,
    })
    mock_gemini.models.generate_content.return_value = mock_res
    monkeypatch.setattr(ai_service, "_client", mock_gemini)
    # ── Step 1: Register ───────────────────────────────────────────────────────
    reg_payload = {
        "email": "e2e_student@example.com",
        "password": "SecurePassword123!",
        "full_name": "Kavipriya Student",
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == reg_payload["email"]

    # ── Step 2: Login ──────────────────────────────────────────────────────────
    login_res = client.post(
        "/auth/login",
        json={"email": reg_payload["email"], "password": reg_payload["password"]},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify /auth/me
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Kavipriya Student"

    # ── Step 3: Create Learning Profile ────────────────────────────────────────
    profile_payload = {
        "education_level": "undergraduate",
        "target_goal": "Python Developer",
        "current_skill_level": "beginner",
        "weekly_hours_available": 12,
        "preferred_learning_style": "hands-on",
    }
    prof_res = client.post("/profile", json=profile_payload, headers=headers)
    assert prof_res.status_code == 201
    assert prof_res.json()["target_goal"] == "Python Developer"

    # ── Step 4: Generate Personalized Learning Map ─────────────────────────────
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer", "force_regenerate": False},
        headers=headers,
    )
    assert map_res.status_code == 201
    learning_map = map_res.json()
    assert len(learning_map["topics"]) >= 3

    topic_1 = learning_map["topics"][0]
    topic_2 = learning_map["topics"][1]
    assert topic_1["progress"]["status"] in ["NOT_STARTED", "IN_PROGRESS"]
    assert topic_2["progress"]["status"] == "LOCKED"

    # ── Step 5: Read Topic 1 Content ───────────────────────────────────────────
    content_res = client.get(f"/topics/{topic_1['id']}/content", headers=headers)
    assert content_res.status_code == 200
    content = content_res.json()
    assert len(content["summary"]) > 10
    assert len(content["explanation"]) > 20
    assert "code_examples" in content

    # ── Step 6: Ask AI Topic Tutor ─────────────────────────────────────────────
    tutor_res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "What is the best way to practice variables and data types in this topic?"},
        headers=headers,
    )
    assert tutor_res.status_code == 200
    tutor_data = tutor_res.json()
    assert tutor_data["is_topic_related"] is True
    assert len(tutor_data["explanation"]) > 20

    # ── Step 7: Take Topic 1 Assessment - Failure Attempt ──────────────────────
    quiz_res = client.get(f"/topics/{topic_1['id']}/assessment", headers=headers)
    assert quiz_res.status_code == 200
    quiz = quiz_res.json()

    # Intentionally submit incorrect answers
    fail_answers = [
        {"question_id": q["id"], "selected_option_index": 3} for q in quiz["questions"]
    ]
    fail_submit = client.post(
        f"/assessments/{quiz['id']}/submit",
        json={"answers": fail_answers},
        headers=headers,
    )
    assert fail_submit.status_code == 200
    fail_report = fail_submit.json()
    assert fail_report["passed"] is False
    assert fail_report["score_percentage"] < 70
    assert fail_report["adaptive_recommendation"]["action"] == "REVIEW_AND_RETAKE"

    # Verify Topic 2 remains LOCKED
    locked_check = client.get(f"/topics/{topic_2['id']}/content", headers=headers)
    assert locked_check.status_code == 403

    # ── Step 8: Retake Topic 1 Assessment - Passing Attempt (100%) ─────────────
    correct_indices = [0, 1, 2, 0, 1, 2, 1, 0, 0, 1, 0, 1, 0, 0, 0]
    pass_answers = [
        {"question_id": q["id"], "selected_option_index": correct_indices[i % len(correct_indices)]}
        for i, q in enumerate(quiz["questions"])
    ]
    pass_submit = client.post(
        f"/assessments/{quiz['id']}/submit",
        json={"answers": pass_answers},
        headers=headers,
    )
    assert pass_submit.status_code == 200
    pass_report = pass_submit.json()
    assert pass_report["passed"] is True
    assert pass_report["score_percentage"] == 100
    assert pass_report["adaptive_recommendation"]["action"] == "PROCEED_TO_NEXT_TOPIC"
    assert pass_report["adaptive_recommendation"]["next_topic_id"] == topic_2["id"]

    # ── Step 9: Advance to Unlocked Topic 2 ─────────────────────────────────────
    topic_2_content = client.get(f"/topics/{topic_2['id']}/content", headers=headers)
    assert topic_2_content.status_code == 200
    assert len(topic_2_content.json()["summary"]) > 10

    # ── Step 10: Verify Progress Dashboard Analytics ───────────────────────────
    dash_res = client.get("/progress/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dashboard = dash_res.json()

    assert dashboard["goal_title"] == "Python Developer"
    assert dashboard["completed_topics_count"] >= 1
    assert dashboard["overall_progress_percentage"] > 0
    assert dashboard["average_score"] is not None
    assert dashboard["current_topic"]["topic_id"] == topic_2["id"]
    assert "recommended" in dashboard["recommendation_reason"].lower()
