"""
AI Topic Tutor Automated Tests.

Validates:
1. Tutor receives current topic context (title, description, difficulty).
2. Tutor receives actual topic content (summary, explanation, code, pitfalls, takeaways).
3. Tutor receives student level and goal.
4. Tutor receives recent conversation history (controlled window).
5. Follow-up questions preserve context across turns.
6. Unrelated questions are handled appropriately (polite redirection).
7. Empty Gemini response is handled (HTTP 502 with Retry).
8. Gemini API failure is handled (timeout HTTP 504, rate limit HTTP 429, missing key HTTP 503).
9. API key is never exposed to frontend responses.
10. Existing security and prerequisite protections (locked topics, empty input, ownership isolation).
"""

from unittest.mock import MagicMock
import json
import pytest
from fastapi.testclient import TestClient

from app.services.ai_service import ai_service
from app.config import settings


def _setup_student_with_topic(client: TestClient, email: str, goal: str = "Python Developer", level: str = "beginner"):
    """Helper to register, login, set profile, and create a learning map."""
    client.post("/auth/register", json={"email": email, "password": "Password123!", "full_name": "Test Student"})
    login_res = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/profile",
        json={
            "education_level": "undergraduate",
            "target_goal": goal,
            "current_skill_level": level,
            "weekly_hours_available": 10,
            "preferred_learning_style": "hands-on",
        },
        headers=headers,
    )
    map_res = client.post("/learning-maps", json={"goal_title": goal, "force_regenerate": False}, headers=headers)
    topics = map_res.json()["topics"]
    return headers, topics[0], topics[1] if len(topics) > 1 else None


def test_tutor_receives_current_topic_context(client: TestClient, monkeypatch):
    """Verify Gemini receives topic title, description, and difficulty level."""
    headers, topic_1, _ = _setup_student_with_topic(client, "context_student@example.com")

    captured_prompt = None

    def fake_generate_content(model, contents, config):
        nonlocal captured_prompt
        captured_prompt = contents
        mock_res = MagicMock()
        mock_res.text = json.dumps({
            "explanation": "Topic explanation tailored to this concept.",
            "is_topic_related": True,
            "code_example": None,
            "common_mistake": None,
            "practice_question": None,
        })
        return mock_res

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = fake_generate_content
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "Explain this topic to me."},
        headers=headers,
    )
    assert res.status_code == 200
    assert captured_prompt is not None
    assert f"Topic Title: {topic_1['title']}" in captured_prompt
    assert f"Topic Difficulty: {topic_1['difficulty']}" in captured_prompt


def test_tutor_receives_actual_topic_content(client: TestClient, monkeypatch):
    """Verify Gemini receives the actual generated lesson content for grounding."""
    headers, topic_1, _ = _setup_student_with_topic(client, "content_student@example.com")

    # Pre-generate content
    content_res = client.get(f"/topics/{topic_1['id']}/content", headers=headers)
    assert content_res.status_code == 200
    content_data = content_res.json()

    captured_prompt = None

    def fake_generate_content(model, contents, config):
        nonlocal captured_prompt
        captured_prompt = contents
        mock_res = MagicMock()
        mock_res.text = json.dumps({
            "explanation": "Grounded explanation based on supplied content.",
            "is_topic_related": True,
            "code_example": "x = 10",
            "common_mistake": "None",
            "practice_question": "What is x?",
        })
        return mock_res

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = fake_generate_content
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "What does the lesson explanation mean?"},
        headers=headers,
    )
    assert res.status_code == 200
    assert captured_prompt is not None
    assert "=== SUPPLIED LESSON CONTENT (PRIMARY EDUCATIONAL GROUNDING) ===" in captured_prompt
    assert content_data["summary"] in captured_prompt or content_data["explanation"][:30] in captured_prompt


def test_tutor_receives_student_level_and_goal(client: TestClient, monkeypatch):
    """Verify Gemini receives the student's skill level and career goal."""
    headers, topic_1, _ = _setup_student_with_topic(
        client, "level_student@example.com", goal="Data Engineer", level="intermediate"
    )

    captured_prompt = None

    def fake_generate_content(model, contents, config):
        nonlocal captured_prompt
        captured_prompt = contents
        mock_res = MagicMock()
        mock_res.text = json.dumps({
            "explanation": "Intermediate level explanation for data engineering.",
            "is_topic_related": True,
            "code_example": None,
            "common_mistake": None,
            "practice_question": None,
        })
        return mock_res

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = fake_generate_content
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "How should I structure this at my level?"},
        headers=headers,
    )
    assert res.status_code == 200
    assert captured_prompt is not None
    assert "Student Learning Level: intermediate" in captured_prompt
    assert "Student Career Goal: Data Engineer" in captured_prompt


def test_tutor_receives_recent_conversation_history(client: TestClient, monkeypatch):
    """Verify Gemini receives the controlled window of prior conversation turns."""
    headers, topic_1, _ = _setup_student_with_topic(client, "history_student@example.com")

    captured_prompt = None

    def fake_generate_content(model, contents, config):
        nonlocal captured_prompt
        captured_prompt = contents
        mock_res = MagicMock()
        mock_res.text = json.dumps({
            "explanation": "Continuing our discussion on loops.",
            "is_topic_related": True,
            "code_example": None,
            "common_mistake": None,
            "practice_question": None,
        })
        return mock_res

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = fake_generate_content
    monkeypatch.setattr(ai_service, "_client", mock_client)

    history = [
        {"role": "user", "content": "What is a while loop?"},
        {"role": "assistant", "content": "A while loop runs as long as a condition is true."},
        {"role": "user", "content": "Can you give an example?"},
        {"role": "assistant", "content": "while count < 5: count += 1"},
    ]

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "Why would that create an infinite loop if count is not incremented?", "conversation_history": history},
        headers=headers,
    )
    assert res.status_code == 200
    assert captured_prompt is not None
    assert "=== RECENT CONVERSATION HISTORY ===" in captured_prompt
    assert "Student: What is a while loop?" in captured_prompt
    assert "Tutor: A while loop runs as long as a condition is true." in captured_prompt


def test_follow_up_questions_preserve_context(client: TestClient, monkeypatch):
    """Verify follow-up queries ('why?', 'explain that again') maintain context."""
    headers, topic_1, _ = _setup_student_with_topic(client, "followup_student@example.com")

    captured_prompt = None

    def fake_generate_content(model, contents, config):
        nonlocal captured_prompt
        captured_prompt = contents
        mock_res = MagicMock()
        mock_res.text = json.dumps({
            "explanation": "Re-explaining the previous concept with an intuitive real-world analogy.",
            "is_topic_related": True,
            "code_example": None,
            "common_mistake": None,
            "practice_question": None,
        })
        return mock_res

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = fake_generate_content
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={
            "question": "I didn't understand. Can you explain that differently?",
            "conversation_history": [
                {"role": "user", "content": "How does memory allocation work in Python?"},
                {"role": "assistant", "content": "Python manages memory with private heaps and reference counts."},
            ],
        },
        headers=headers,
    )
    assert res.status_code == 200
    assert "Re-explaining the previous concept" in res.json()["explanation"]
    assert "How does memory allocation work in Python?" in captured_prompt


def test_unrelated_questions_handled_appropriately(client: TestClient, monkeypatch):
    """Verify off-topic questions return is_topic_related=False and a polite redirect."""
    headers, topic_1, _ = _setup_student_with_topic(client, "unrelated_student@example.com")

    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.text = json.dumps({
        "explanation": f"That topic is outside our current lesson on {topic_1['title']}. Let's focus on mastering {topic_1['title']}! What would you like to explore about this lesson?",
        "is_topic_related": False,
        "code_example": None,
        "common_mistake": None,
        "practice_question": None,
    })
    mock_client.models.generate_content.return_value = mock_res
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "What is the best recipe for baking chocolate cake?"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_topic_related"] is False
    assert "outside our current lesson" in data["explanation"].lower() or "focus" in data["explanation"].lower()


def test_empty_gemini_response_handled(client: TestClient, monkeypatch):
    """Verify empty Gemini response returns HTTP 502 with Retry message."""
    headers, topic_1, _ = _setup_student_with_topic(client, "empty_student@example.com")

    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.text = ""  # Empty text
    mock_client.models.generate_content.return_value = mock_res
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "Explain this concept."},
        headers=headers,
    )
    assert res.status_code == 502
    assert "empty response" in res.json()["detail"].lower()
    assert "retry" in res.json()["detail"].lower()


def test_gemini_api_failure_handled(client: TestClient, monkeypatch):
    """Verify Gemini API exceptions return clear error with Retry, not fake answers."""
    headers, topic_1, _ = _setup_student_with_topic(client, "failure_student@example.com")

    # 1. Timeout error -> HTTP 504
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Connection to Gemini timed out")
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res_timeout = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "Explain this concept."},
        headers=headers,
    )
    assert res_timeout.status_code == 504
    assert "timed out" in res_timeout.json()["detail"].lower()
    assert "retry" in res_timeout.json()["detail"].lower()

    # 2. Rate limit error -> HTTP 429
    mock_client.models.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded")
    res_rate = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "Explain this concept."},
        headers=headers,
    )
    assert res_rate.status_code == 429
    assert "rate limit" in res_rate.json()["detail"].lower()

    # 3. Missing API key -> HTTP 503
    monkeypatch.setattr(ai_service, "_client", None)
    monkeypatch.setattr(ai_service, "api_key", "")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    res_missing = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "Explain this concept."},
        headers=headers,
    )
    assert res_missing.status_code == 503
    assert "gemini api key is not configured" in res_missing.json()["detail"].lower()


def test_api_key_not_exposed_to_frontend(client: TestClient, monkeypatch):
    """Verify the Gemini API key is never exposed in response payloads or headers."""
    headers, topic_1, _ = _setup_student_with_topic(client, "security_student@example.com")

    secret_key = "AIzaSyFakeSecretKeyThatMustNeverBeExposed"
    monkeypatch.setattr(settings, "GEMINI_API_KEY", secret_key)

    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.text = json.dumps({
        "explanation": "Secure tutor explanation.",
        "is_topic_related": True,
        "code_example": None,
        "common_mistake": None,
        "practice_question": None,
    })
    mock_client.models.generate_content.return_value = mock_res
    monkeypatch.setattr(ai_service, "_client", mock_client)

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "How does security work?"},
        headers=headers,
    )
    assert res.status_code == 200
    response_text = res.text
    assert secret_key not in response_text
    for header_name, header_val in res.headers.items():
        assert secret_key not in header_val


def test_locked_topic_forbidden(client: TestClient):
    """Cannot access AI tutor on a LOCKED topic (HTTP 403)."""
    headers, _, topic_2 = _setup_student_with_topic(client, "locked_student@example.com")
    assert topic_2 is not None

    res = client.post(
        f"/topics/{topic_2['id']}/tutor",
        json={"question": "Can you explain this locked topic?"},
        headers=headers,
    )
    assert res.status_code == 403
    assert "locked" in res.json()["detail"].lower()


def test_empty_question_validation(client: TestClient):
    """Empty or whitespace-only question is rejected with HTTP 422."""
    headers, topic_1, _ = _setup_student_with_topic(client, "empty_q_student@example.com")

    res = client.post(
        f"/topics/{topic_1['id']}/tutor",
        json={"question": "   "},
        headers=headers,
    )
    assert res.status_code == 422


def test_unauthorized_isolation(client: TestClient):
    """Student B cannot query AI tutor for Student A's topic (HTTP 404)."""
    headers_a, topic_a, _ = _setup_student_with_topic(client, "student_a@example.com")
    headers_b, _, _ = _setup_student_with_topic(client, "student_b@example.com")

    res = client.post(
        f"/topics/{topic_a['id']}/tutor",
        json={"question": "How does inheritance work?"},
        headers=headers_b,
    )
    assert res.status_code == 404


def test_unauthenticated_access(client: TestClient):
    """Calling tutor endpoint without JWT returns HTTP 401."""
    res = client.post(
        "/topics/any-fake-topic-id/tutor",
        json={"question": "How does this work?"},
    )
    assert res.status_code == 401
