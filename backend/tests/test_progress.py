"""
Unit and Integration Tests for Progress Tracking and Dashboard Analytics.

Tests deterministic progress calculations, sequential prerequisite unlocking,
dynamic resolution of the "Continue Learning" target, and completion metrics.
"""


def get_auth_headers(client, email: str, password: str = "Password123", name: str = "Student") -> dict:
    """Helper to register and log in a user, returning Bearer auth header."""
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    res = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_analytics_initial_state(client):
    """Verify that a newly created roadmap starts with 0% progress and Topic 1 as the current topic."""
    headers = get_auth_headers(client, "dash_user1@example.com")
    client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )

    response = client.get("/progress/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["goal_title"] == "Java Backend Developer"
    assert data["overall_progress_percentage"] == 0
    assert data["completed_topics_count"] == 0
    assert data["total_topics_count"] >= 4

    # Current topic must be Topic 1
    assert data["current_topic"] is not None
    assert data["current_topic"]["sequence_order"] == 1
    assert data["current_topic"]["status"] == "NOT_STARTED"
    assert "prerequisite" in data["recommendation_reason"].lower()


def test_complete_topic_and_unlock_next(client):
    """Verify that completing Topic 1 automatically unlocks Topic 2 (LOCKED -> NOT_STARTED)."""
    headers = get_auth_headers(client, "unlock_user@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )
    topics = map_res.json()["topics"]
    topic_1_id = topics[0]["id"]
    topic_2_id = topics[1]["id"]

    # Verify initial statuses
    assert topics[0]["progress"]["status"] == "NOT_STARTED"
    assert topics[1]["progress"]["status"] == "LOCKED"

    # Complete Topic 1
    complete_res = client.post(
        f"/topics/{topic_1_id}/complete",
        json={"mastery_score": 90},
        headers=headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
    assert complete_res.json()["mastery_score"] == 90

    # Verify Topic 2 is now unlocked (NOT_STARTED)
    topic_2_details = client.get(f"/topics/{topic_2_id}", headers=headers).json()
    assert topic_2_details["progress"]["status"] == "NOT_STARTED"


def test_dashboard_reflects_progress_advance(client):
    """Verify that dashboard percentage and current topic update accurately upon topic completion."""
    headers = get_auth_headers(client, "dash_user2@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer"},
        headers=headers,
    )
    topics = map_res.json()["topics"]
    total_topics = len(topics)
    topic_1_id = topics[0]["id"]
    topic_2_id = topics[1]["id"]

    # Complete 1st topic
    client.post(f"/topics/{topic_1_id}/complete", headers=headers)

    # Open content of 2nd topic (transitions to IN_PROGRESS)
    client.get(f"/topics/{topic_2_id}/content", headers=headers)

    dash_res = client.get("/progress/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()

    expected_pct = int((1 / total_topics) * 100)
    assert dash_data["overall_progress_percentage"] == expected_pct
    assert dash_data["completed_topics_count"] == 1

    # Current topic must now point to Topic 2 with status IN_PROGRESS
    assert dash_data["current_topic"]["topic_id"] == topic_2_id
    assert dash_data["current_topic"]["sequence_order"] == 2
    assert dash_data["current_topic"]["status"] == "IN_PROGRESS"


def test_cannot_complete_locked_topic(client):
    """Verify attempting to complete a locked topic directly returns HTTP 400 Bad Request."""
    headers = get_auth_headers(client, "lock_err_user@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )
    topic_3_id = map_res.json()["topics"][2]["id"]

    response = client.post(f"/topics/{topic_3_id}/complete", headers=headers)
    assert response.status_code == 400
    assert "locked" in response.json()["detail"].lower()


def test_complete_all_topics_achieves_100_percent(client):
    """Verify completing all topics achieves 100% progress and sets current_topic to None."""
    headers = get_auth_headers(client, "mastery_user@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Web Development"},
        headers=headers,
    )
    topics = map_res.json()["topics"]

    for t in topics:
        client.post(f"/topics/{t['id']}/complete", headers=headers)

    dash_res = client.get("/progress/dashboard", headers=headers)
    dash_data = dash_res.json()

    assert dash_data["overall_progress_percentage"] == 100
    assert dash_data["completed_topics_count"] == len(topics)
    assert dash_data["current_topic"] is None
    assert "congratulations" in dash_data["recommendation_reason"].lower()


def test_dashboard_without_active_map_returns_404(client):
    """Verify GET /progress/dashboard returns 404 if no roadmap was initialized."""
    headers = get_auth_headers(client, "empty_dash_user@example.com")
    response = client.get("/progress/dashboard", headers=headers)
    assert response.status_code == 404
