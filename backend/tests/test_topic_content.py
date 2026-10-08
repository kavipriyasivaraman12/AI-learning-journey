"""
Unit and Integration Tests for Topic Content Generation & Caching.

Tests content generation, PostgreSQL persistent caching, automatic status advancement,
prerequisite lock enforcement, and cross-user ownership isolation.
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


def test_get_topic_details_success(client):
    """Verify GET /topics/{id} returns topic details and progress."""
    headers = get_auth_headers(client, "topic_user1@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )
    topic_1 = map_res.json()["topics"][0]

    response = client.get(f"/topics/{topic_1['id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == topic_1["id"]
    assert data["sequence_order"] == 1
    assert data["progress"]["status"] == "NOT_STARTED"
    assert data["has_content"] is False


def test_generate_and_cache_topic_content(client):
    """Verify first visit generates content and saves it, while second visit hits PostgreSQL cache."""
    headers = get_auth_headers(client, "content_user@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )
    topic_1 = map_res.json()["topics"][0]
    topic_id = topic_1["id"]

    # First request: Generates content & caches to DB
    res1 = client.get(f"/topics/{topic_id}/content", headers=headers)
    assert res1.status_code == 200
    content1 = res1.json()
    assert content1["topic_id"] == topic_id
    assert len(content1["explanation"]) > 20
    assert len(content1["code_examples"]) > 10
    assert len(content1["key_takeaways"]) > 10

    # Second request: Serves from PostgreSQL cache (Reuse)
    res2 = client.get(f"/topics/{topic_id}/content", headers=headers)
    assert res2.status_code == 200
    content2 = res2.json()

    # Content IDs and timestamps must match exactly
    assert content1["id"] == content2["id"]
    assert content1["generated_at"] == content2["generated_at"]


def test_topic_status_advances_to_in_progress(client):
    """Verify accessing content updates topic progress status from NOT_STARTED to IN_PROGRESS."""
    headers = get_auth_headers(client, "progress_user@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Python Developer"},
        headers=headers,
    )
    topic_1 = map_res.json()["topics"][0]
    topic_id = topic_1["id"]

    # Before viewing content -> NOT_STARTED
    details_before = client.get(f"/topics/{topic_id}", headers=headers).json()
    assert details_before["progress"]["status"] == "NOT_STARTED"

    # View content
    client.get(f"/topics/{topic_id}/content", headers=headers)

    # After viewing content -> IN_PROGRESS
    details_after = client.get(f"/topics/{topic_id}", headers=headers).json()
    assert details_after["progress"]["status"] == "IN_PROGRESS"


def test_locked_topic_content_access_forbidden(client):
    """Verify attempting to view content of a LOCKED topic returns HTTP 403 Forbidden."""
    headers = get_auth_headers(client, "locked_user@example.com")
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )
    # Topic 2 starts as LOCKED
    topic_2 = map_res.json()["topics"][1]
    assert topic_2["progress"]["status"] == "LOCKED"

    response = client.get(f"/topics/{topic_2['id']}/content", headers=headers)
    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()


def test_cross_user_topic_access_rejected(client):
    """Verify User B cannot access User A's topic details or content."""
    headers_a = get_auth_headers(client, "user_a_topic@example.com", name="User A")
    headers_b = get_auth_headers(client, "user_b_topic@example.com", name="User B")

    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers_a,
    )
    topic_1_id = map_res.json()["topics"][0]["id"]

    # User B attempts to access User A's topic
    res_details = client.get(f"/topics/{topic_1_id}", headers=headers_b)
    assert res_details.status_code == 404

    res_content = client.get(f"/topics/{topic_1_id}/content", headers=headers_b)
    assert res_content.status_code == 404
