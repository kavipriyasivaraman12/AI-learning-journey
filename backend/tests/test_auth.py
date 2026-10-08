"""
Unit and Integration Tests for Authentication System.

Tests user registration, validation, duplicate rejection, login,
password hashing, JWT issuance, and protected /auth/me route access.
"""


def test_register_user_success(client):
    """Verify that a student can successfully register with valid details."""
    payload = {
        "email": "student@example.com",
        "password": "StrongPassword123",
        "full_name": "Test Student",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["full_name"] == "Test Student"
    assert "id" in data
    assert len(data["id"]) == 36  # Valid UUIDv4 length
    # CRITICAL: Verify plain/hashed password is never returned in response
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    """Verify that registering the same email twice returns HTTP 400 Bad Request."""
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123",
        "full_name": "First User",
    }
    # First registration
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_invalid_email_format(client):
    """Verify that invalid email strings are rejected with 422 Unprocessable Entity."""
    payload = {
        "email": "invalid-email-format",
        "password": "StrongPassword123",
        "full_name": "Invalid User",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_register_short_password_fails(client):
    """Verify that passwords shorter than 8 characters are rejected."""
    payload = {
        "email": "user@example.com",
        "password": "short",  # Less than 8 chars
        "full_name": "User",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success(client):
    """Verify that a registered student can log in and receive a JWT token."""
    # 1. Register user
    reg_payload = {
        "email": "login_test@example.com",
        "password": "MySecretPassword123",
        "full_name": "Login Tester",
    }
    client.post("/auth/register", json=reg_payload)

    # 2. Log in
    login_payload = {
        "email": "login_test@example.com",
        "password": "MySecretPassword123",
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_test@example.com"


def test_login_incorrect_password_fails(client):
    """Verify that logging in with the wrong password returns HTTP 401 Unauthorized."""
    # 1. Register user
    reg_payload = {
        "email": "wrong_pwd@example.com",
        "password": "CorrectPassword123",
        "full_name": "Tester",
    }
    client.post("/auth/register", json=reg_payload)

    # 2. Attempt login with wrong password
    login_payload = {
        "email": "wrong_pwd@example.com",
        "password": "WrongPassword456",
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user_fails(client):
    """Verify that logging in with an unregistered email returns HTTP 401."""
    login_payload = {
        "email": "ghost@example.com",
        "password": "AnyPassword123",
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401


def test_get_current_user_profile_with_jwt(client):
    """Verify that /auth/me returns user data when supplied with a valid JWT token."""
    # 1. Register
    reg_payload = {
        "email": "profile@example.com",
        "password": "SecurePassword123",
        "full_name": "Profile User",
    }
    client.post("/auth/register", json=reg_payload)

    # 2. Login to get token
    login_res = client.post(
        "/auth/login",
        json={"email": "profile@example.com", "password": "SecurePassword123"},
    )
    token = login_res.json()["access_token"]

    # 3. Access protected /auth/me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "profile@example.com"
    assert data["full_name"] == "Profile User"


def test_get_current_user_without_token_fails(client):
    """Verify that accessing /auth/me without an Authorization header returns HTTP 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert "missing" in response.json()["detail"].lower()


def test_get_current_user_with_invalid_token_fails(client):
    """Verify that accessing /auth/me with a tampered or invalid token returns HTTP 401."""
    headers = {"Authorization": "Bearer invalid.fake.token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
