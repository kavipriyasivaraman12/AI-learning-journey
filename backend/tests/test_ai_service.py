"""
Unit Tests for AI Service Layer and Gemini Integration.

Validates structured JSON schema generation, token-efficient prompting,
mock Gemini API responses, and resilient fallback error handling.
"""

from unittest.mock import MagicMock
import json
from app.services.ai_service import AIService, AIRoadmapResponse


def test_ai_service_fallback_without_api_key():
    """Verify that AIService safely falls back to domain templates when no API key is provided."""
    service = AIService(api_key="")
    assert service.is_available() is False

    roadmap = service.generate_learning_roadmap("Java Backend Developer")
    assert isinstance(roadmap, AIRoadmapResponse)
    assert len(roadmap.topics) >= 4
    assert roadmap.topics[0].sequence_order == 1
    assert roadmap.topics[0].title != ""


def test_ai_service_mocked_gemini_success():
    """Verify that AIService successfully validates and structures a compliant JSON response from Gemini."""
    service = AIService(api_key="mock_test_key")
    # Mock Google GenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Cloud Native Go Developer",
        "description": "Roadmap for mastering Golang and Microservices",
        "topics": [
            {
                "title": "Go Syntax & Concurrency with Goroutines",
                "description": "Channels, Goroutines, Select statements, and Mutexes.",
                "sequence_order": 1,
                "difficulty": "Beginner",
                "estimated_minutes": 60,
            },
            {
                "title": "Building Microservices with gRPC",
                "description": "Protocol Buffers, RPC endpoints, and service discovery.",
                "sequence_order": 2,
                "difficulty": "Intermediate",
                "estimated_minutes": 90,
            },
        ],
    })
    mock_client.models.generate_content.return_value = mock_response
    service._client = mock_client

    result = service.generate_learning_roadmap("Cloud Native Go Developer")
    assert result.title == "Cloud Native Go Developer"
    assert len(result.topics) == 2
    assert result.topics[0].title == "Go Syntax & Concurrency with Goroutines"
    assert result.topics[1].sequence_order == 2


def test_ai_service_malformed_json_fallback():
    """Verify that AIService gracefully falls back if Gemini returns invalid/non-JSON text."""
    service = AIService(api_key="mock_test_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is plain text and completely invalid JSON"
    mock_client.models.generate_content.return_value = mock_response
    service._client = mock_client

    result = service.generate_learning_roadmap("Python Developer")
    # Must not crash; must return fallback roadmap
    assert isinstance(result, AIRoadmapResponse)
    assert len(result.topics) > 0


def test_ai_service_api_exception_fallback():
    """Verify that AIService catches API errors (rate limits, timeouts) and activates fallback."""
    service = AIService(api_key="mock_test_key")
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("429 Resource Exhausted / Rate limit")
    service._client = mock_client

    result = service.generate_learning_roadmap("Machine Learning Engineer")
    # Must catch the exception cleanly and return fallback
    assert isinstance(result, AIRoadmapResponse)
    assert len(result.topics) > 0


def test_end_to_end_roadmap_creation_with_ai_integration(client):
    """Verify end-to-end endpoint execution invoking learning service with AI integration."""
    # Register & login
    client.post(
        "/auth/register",
        json={"email": "ai_map_user@example.com", "password": "Password123", "full_name": "AI Tester"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "ai_map_user@example.com", "password": "Password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Request roadmap
    response = client.post(
        "/learning-maps",
        json={"goal_title": "Full Stack Web Developer"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal_title"] == "Full Stack Web Developer"
    assert len(data["topics"]) >= 4
    assert data["topics"][0]["progress"]["status"] == "NOT_STARTED"
    assert data["topics"][1]["progress"]["status"] == "LOCKED"
