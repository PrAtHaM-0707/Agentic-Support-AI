def test_signup(client):
    response = client.post(
        "/auth/signup",
        json={
            "email": "testuser@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_signup_duplicate_email(client):
    # First user
    client.post(
        "/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    # Attempt duplicate
    response = client.post(
        "/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login(client):
    # Create user
    client.post(
        "/auth/signup",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
