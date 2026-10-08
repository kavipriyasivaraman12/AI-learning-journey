"""
Unit and Integration Tests for Learning Profile Management.

Tests profile creation, retrieval, updates, 1:1 uniqueness constraint,
cross-user isolation, validation, and JWT authorization requirements.
"""


def get_auth_headers(client, email: str, password: str = "Password123", name: str = "Student") -> dict:
    """Helper to register and log in a user, returning the Bearer auth header."""
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


def test_get_profile_not_created_returns_404(client):
    """Verify that GET /profile returns 404 if profile has not yet been initialized."""
    headers = get_auth_headers(client, "newbie@example.com")
    response = client.get("/profile", headers=headers)
    assert response.status_code == 404
    assert "not been created" in response.json()["detail"].lower()


def test_create_profile_success(client):
    """Verify that a student can successfully initialize their learning profile."""
    headers = get_auth_headers(client, "student1@example.com")
    payload = {
        "education_level": "3rd Year CSE Undergraduate",
        "target_goal": "Java Backend Developer",
        "current_skill_level": "Beginner",
        "weekly_hours_available": 15,
        "preferred_learning_style": "Practical / Projects",
    }
    response = client.post("/profile", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["target_goal"] == "Java Backend Developer"
    assert data["weekly_hours_available"] == 15
    assert "id" in data
    assert "user_id" in data


def test_create_duplicate_profile_fails(client):
    """Verify that attempting to create a second profile returns HTTP 400 Bad Request."""
    headers = get_auth_headers(client, "single_profile@example.com")
    payload = {
        "education_level": "Undergraduate",
        "target_goal": "Full Stack Web Developer",
        "current_skill_level": "Intermediate",
        "weekly_hours_available": 10,
        "preferred_learning_style": "Practical",
    }
    # First creation -> Success
    res1 = client.post("/profile", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second creation -> Rejection
    res2 = client.post("/profile", json=payload, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_get_profile_success(client):
    """Verify that GET /profile returns the authenticated student's profile."""
    headers = get_auth_headers(client, "viewer@example.com")
    payload = {
        "education_level": "Graduate",
        "target_goal": "Data Scientist",
        "current_skill_level": "Beginner",
        "weekly_hours_available": 20,
        "preferred_learning_style": "Visual",
    }
    client.post("/profile", json=payload, headers=headers)

    response = client.get("/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["target_goal"] == "Data Scientist"
    assert data["education_level"] == "Graduate"
    assert data["weekly_hours_available"] == 20


def test_update_profile_success(client):
    """Verify that PUT /profile selectively updates profile fields."""
    headers = get_auth_headers(client, "updater@example.com")
    init_payload = {
        "education_level": "Undergraduate",
        "target_goal": "Python Developer",
        "current_skill_level": "Beginner",
        "weekly_hours_available": 10,
        "preferred_learning_style": "Practical",
    }
    client.post("/profile", json=init_payload, headers=headers)

    # Update target goal and weekly hours
    update_payload = {
        "target_goal": "Senior Python Backend Architect",
        "weekly_hours_available": 25,
    }
    response = client.put("/profile", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["target_goal"] == "Senior Python Backend Architect"
    assert data["weekly_hours_available"] == 25
    # Unmodified fields should remain unchanged
    assert data["education_level"] == "Undergraduate"
    assert data["current_skill_level"] == "Beginner"


def test_update_profile_not_found(client):
    """Verify that PUT /profile returns 404 if profile does not exist yet."""
    headers = get_auth_headers(client, "no_profile_updater@example.com")
    response = client.put(
        "/profile",
        json={"target_goal": "New Goal"},
        headers=headers,
    )
    assert response.status_code == 404


def test_profile_endpoints_require_authentication(client):
    """Verify that unauthenticated requests to /profile are rejected with 401."""
    assert client.get("/profile").status_code == 401
    assert client.post("/profile", json={}).status_code == 401
    assert client.put("/profile", json={}).status_code == 401


def test_profile_isolation_between_users(client):
    """Verify that User A and User B cannot see or overwrite each other's profiles."""
    headers_a = get_auth_headers(client, "user_a@example.com", name="User A")
    headers_b = get_auth_headers(client, "user_b@example.com", name="User B")

    client.post(
        "/profile",
        json={
            "education_level": "Undergraduate",
            "target_goal": "Goal User A",
            "current_skill_level": "Beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "Practical",
        },
        headers=headers_a,
    )

    client.post(
        "/profile",
        json={
            "education_level": "Graduate",
            "target_goal": "Goal User B",
            "current_skill_level": "Advanced",
            "weekly_hours_available": 30,
            "preferred_learning_style": "Theoretical",
        },
        headers=headers_b,
    )

    res_a = client.get("/profile", headers=headers_a)
    res_b = client.get("/profile", headers=headers_b)

    assert res_a.json()["target_goal"] == "Goal User A"
    assert res_b.json()["target_goal"] == "Goal User B"
    assert res_a.json()["user_id"] != res_b.json()["user_id"]
