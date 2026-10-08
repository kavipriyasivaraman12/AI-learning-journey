"""
Unit and Integration Tests for Learning Map and Roadmap Management.

Tests roadmap generation, topic sequence ordering, automatic progress initialization,
roadmap reuse logic, force regeneration, active roadmap retrieval, and ownership isolation.
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


def test_generate_learning_map_from_explicit_goal(client):
    """Verify generating a roadmap with an explicit goal creates ordered topics and progress."""
    headers = get_auth_headers(client, "map_user1@example.com")
    payload = {"goal_title": "Java Backend Developer"}
    response = client.post("/learning-maps", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["goal_title"] == "Java Backend Developer"
    assert data["is_active"] is True
    assert len(data["topics"]) >= 4

    # Verify topic ordering and progression rules
    first_topic = data["topics"][0]
    assert first_topic["sequence_order"] == 1
    assert first_topic["progress"]["status"] == "NOT_STARTED"

    # All subsequent topics must start in LOCKED status
    for topic in data["topics"][1:]:
        assert topic["sequence_order"] > 1
        assert topic["progress"]["status"] == "LOCKED"


def test_generate_learning_map_from_profile_goal(client):
    """Verify that omitting goal_title automatically falls back to the student profile goal."""
    headers = get_auth_headers(client, "map_user2@example.com")

    # 1. Create profile with target goal
    client.post(
        "/profile",
        json={
            "education_level": "Undergraduate",
            "target_goal": "Python Developer",
            "current_skill_level": "Beginner",
            "weekly_hours_available": 10,
            "preferred_learning_style": "Practical",
        },
        headers=headers,
    )

    # 2. Generate roadmap without specifying goal_title
    response = client.post("/learning-maps", json={}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["goal_title"] == "Python Developer"
    assert len(data["topics"]) > 0


def test_generate_map_without_goal_or_profile_fails(client):
    """Verify that generating a roadmap with no goal and no profile returns HTTP 400."""
    headers = get_auth_headers(client, "no_goal_user@example.com")
    response = client.post("/learning-maps", json={}, headers=headers)
    assert response.status_code == 400
    assert "specify a goal_title" in response.json()["detail"].lower()


def test_reuse_existing_active_roadmap(client):
    """Verify that repeated requests for the same active goal reuse the existing map."""
    headers = get_auth_headers(client, "reuse_user@example.com")
    payload = {"goal_title": "Web Development"}

    # First request -> Generates new map
    res1 = client.post("/learning-maps", json=payload, headers=headers)
    assert res1.status_code == 201
    map_id_1 = res1.json()["id"]

    # Second request with same goal -> Reuses existing map
    res2 = client.post("/learning-maps", json=payload, headers=headers)
    assert res2.status_code == 201
    map_id_2 = res2.json()["id"]

    # Critical requirement: Both IDs must match (Zero redundant generation)
    assert map_id_1 == map_id_2


def test_force_regenerate_deactivates_old_map(client):
    """Verify that force_regenerate=True creates a fresh map and deactivates the previous one."""
    headers = get_auth_headers(client, "regen_user@example.com")
    payload = {"goal_title": "Java Backend Developer"}

    # First generation
    res1 = client.post("/learning-maps", json=payload, headers=headers)
    map1_id = res1.json()["id"]

    # Force regeneration
    res2 = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer", "force_regenerate": True},
        headers=headers,
    )
    map2_id = res2.json()["id"]

    assert map1_id != map2_id
    assert res2.json()["is_active"] is True

    # Verify old map is deactivated
    old_map_res = client.get(f"/learning-maps/{map1_id}", headers=headers)
    assert old_map_res.json()["is_active"] is False


def test_get_active_roadmap_endpoint(client):
    """Verify GET /learning-maps/active retrieves the active map."""
    headers = get_auth_headers(client, "active_user@example.com")
    client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer"},
        headers=headers,
    )

    response = client.get("/learning-maps/active", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["goal_title"] == "Java Backend Developer"
    assert data["is_active"] is True


def test_get_active_roadmap_not_found(client):
    """Verify GET /learning-maps/active returns 404 if no roadmap was created."""
    headers = get_auth_headers(client, "empty_user@example.com")
    response = client.get("/learning-maps/active", headers=headers)
    assert response.status_code == 404


def test_get_roadmap_by_id_ownership_isolation(client):
    """Verify that students cannot access other students' roadmaps by ID."""
    headers_a = get_auth_headers(client, "user_a_map@example.com", name="User A")
    headers_b = get_auth_headers(client, "user_b_map@example.com", name="User B")

    res_a = client.post(
        "/learning-maps",
        json={"goal_title": "Track A"},
        headers=headers_a,
    )
    map_a_id = res_a.json()["id"]

    # User B attempts to access User A's roadmap
    unauthorized_res = client.get(f"/learning-maps/{map_a_id}", headers=headers_b)
    assert unauthorized_res.status_code == 404


def test_list_student_roadmaps(client):
    """Verify GET /learning-maps lists all roadmaps for the student."""
    headers = get_auth_headers(client, "multi_map_user@example.com")

    # Create map 1
    client.post(
        "/learning-maps",
        json={"goal_title": "Track 1", "force_regenerate": True},
        headers=headers,
    )
    # Create map 2
    client.post(
        "/learning-maps",
        json={"goal_title": "Track 2", "force_regenerate": True},
        headers=headers,
    )

    response = client.get("/learning-maps", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["total_topics"] > 0


def test_advance_next_level_progression(client):
    """Verify progressing from Beginner roadmap to Intermediate roadmap when all topics are completed."""
    headers = get_auth_headers(client, "tier_user@example.com")
    # 1. Create beginner map
    map_res = client.post(
        "/learning-maps",
        json={"goal_title": "Java Backend Developer", "learning_level": "beginner"},
        headers=headers,
    )
    assert map_res.status_code == 201
    beg_map = map_res.json()
    assert beg_map["learning_level"] == "beginner"

    # Attempt advancing before completion fails with 400
    premature_res = client.post("/learning-maps/next-level", headers=headers)
    assert premature_res.status_code == 400

    # Complete all topics
    for topic in beg_map["topics"]:
        comp_res = client.post(f"/topics/{topic['id']}/complete", headers=headers)
        assert comp_res.status_code == 200

    # Advance to next level (Intermediate)
    adv_res = client.post("/learning-maps/next-level", headers=headers)
    assert adv_res.status_code == 201
    inter_map = adv_res.json()
    assert inter_map["learning_level"] == "intermediate"
    assert inter_map["is_active"] is True
    assert len(inter_map["topics"]) >= 20

