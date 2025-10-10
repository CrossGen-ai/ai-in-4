import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, UTC

from db.models import MagicLink
from services.magic_link import serializer
from core.config import settings


# Helper for creating valid test data
VALID_USER_DATA = {
    "email": "test@example.com",
    "name": "Test User",
    "employment_status": "Student",
    "primary_use_context": "Educational purposes",
    "tried_ai_before": True,
    "usage_frequency": "Weekly",
    "comfort_level": 3,
    "goals": ["Learning new skills", "Personal productivity/organization", "Research and information gathering"],
    "learning_preference": "Hands-on practice with examples"
}


def test_register_creates_user_and_sends_magic_link(client):
    """Test user registration creates user and experience profile."""
    with patch("api.routes.auth.send_magic_link_email", new_callable=AsyncMock) as mock_send:
        test_data = {**VALID_USER_DATA, "email": "newuser@example.com"}
        response = client.post("/api/auth/register", json=test_data)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert "id" in data["user"]
        mock_send.assert_called_once()


def test_register_fails_with_duplicate_email(client):
    """Test registration fails when user already exists."""
    test_data = {**VALID_USER_DATA, "email": "duplicate@example.com"}

    # First registration
    with patch("api.routes.auth.send_magic_link_email", new_callable=AsyncMock):
        client.post("/api/auth/register", json=test_data)

    # Second registration with same email
    with patch("api.routes.auth.send_magic_link_email", new_callable=AsyncMock):
        response = client.post("/api/auth/register", json=test_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


def test_register_fails_with_empty_email(client):
    """Test registration fails with invalid email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "",
            "experience_level": "Beginner",
            "background": "Student",
            "goals": "Learn"
        }
    )

    assert response.status_code == 422  # Validation error


def test_register_fails_with_invalid_email_format(client):
    """Test registration fails with malformed email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "experience_level": "Beginner",
            "background": "Student",
            "goals": "Learn"
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_magic_link_request_for_existing_user(client, test_db):
    """Test magic link request endpoint for existing users."""
    # Create user directly without triggering magic link creation
    from services.user_service import create_user
    from models.schemas import UserCreate


    user_data = UserCreate(
        email="existing@example.com",
        name="Test User",
        employment_status="Student",
        primary_use_context="Educational purposes",
        tried_ai_before=True,
        usage_frequency="Weekly",
        comfort_level=3,
        goals=["Learning new skills", "Personal productivity/organization", "Research and information gathering"],
        learning_preference="Hands-on practice with examples"
    )
    await create_user(user_data, test_db)

    # Request magic link
    with patch("api.routes.auth.send_magic_link_email", new_callable=AsyncMock) as mock_send:
        response = client.post(
            "/api/auth/magic-link",
            json={"email": "existing@example.com"}
        )

        assert response.status_code == 200
        assert "magic link has been sent" in response.json()["message"]
        mock_send.assert_called_once()


def test_magic_link_request_for_nonexistent_user(client):
    """Test magic link request for non-existent user doesn't reveal user existence."""
    response = client.post(
        "/api/auth/magic-link",
        json={"email": "nonexistent@example.com"}
    )

    assert response.status_code == 200
    assert "magic link has been sent" in response.json()["message"]


@pytest.mark.asyncio
async def test_magic_link_validation_succeeds_with_valid_token(client, test_db, test_user):
    """Test magic link validation succeeds with valid token."""
    # Generate magic link token
    token = serializer.dumps(test_user.email, salt="magic-link")
    # Use UTC timezone-aware datetimes (service uses UTC for comparison)
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=15)

    magic_link = MagicLink(
        user_id=test_user.id,
        token=token,
        expires_at=expires_at,
        created_at=now,
        used=False
    )
    test_db.add(magic_link)
    await test_db.commit()

    # Validate token
    response = client.post(
        "/api/auth/validate",
        json={"token": token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user.email

    # Verify magic link was marked as used
    await test_db.refresh(magic_link)
    assert magic_link.used is True


@pytest.mark.asyncio
async def test_magic_link_validation_fails_with_expired_token(client, test_db, test_user):
    """Test magic link validation fails with expired token."""
    # Generate token with past expiry
    token = serializer.dumps(test_user.email, salt="magic-link")
    now = datetime.now(UTC)
    expires_at = now - timedelta(minutes=1)  # Expired

    magic_link = MagicLink(
        user_id=test_user.id,
        token=token,
        expires_at=expires_at,
        created_at=now,
        used=False
    )
    test_db.add(magic_link)
    await test_db.commit()

    # Attempt to validate
    response = client.post(
        "/api/auth/validate",
        json={"token": token}
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_magic_link_validation_fails_with_used_token(client, test_db, test_user):
    """Test magic link validation fails with already used token."""
    # Generate token that's already been used
    token = serializer.dumps(test_user.email, salt="magic-link")
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=15)

    magic_link = MagicLink(
        user_id=test_user.id,
        token=token,
        expires_at=expires_at,
        created_at=now,
        used=True  # Already used
    )
    test_db.add(magic_link)
    await test_db.commit()

    # Attempt to validate
    response = client.post(
        "/api/auth/validate",
        json={"token": token}
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_validate_endpoint_with_invalid_token(client):
    """Test validate endpoint with completely invalid token."""
    response = client.post(
        "/api/auth/validate",
        json={"token": "completely-invalid-token"}
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_validate_endpoint_with_token_not_in_database(client):
    """Test validate endpoint with valid signature but token not in database."""
    # Generate a valid token but don't store it in database
    token = serializer.dumps("orphan@example.com", salt="magic-link")

    response = client.post(
        "/api/auth/validate",
        json={"token": token}
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_logout_endpoint(client):
    """Test logout endpoint returns success."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "Logged out successfully" in response.json()["message"]


@pytest.mark.asyncio
async def test_dev_users_endpoint_in_dev_mode(client, test_db, test_user):
    """Test dev-users endpoint returns user list in dev mode."""
    with patch.object(settings, "DEV_MODE", True):
        response = client.get("/api/auth/dev-users")

        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1
        assert any(u["email"] == test_user.email for u in users)


def test_dev_users_endpoint_blocked_in_production(client):
    """Test dev-users endpoint is blocked in production mode."""
    with patch.object(settings, "DEV_MODE", False):
        response = client.get("/api/auth/dev-users")

        assert response.status_code == 404
        assert "Not available in production" in response.json()["detail"]


@pytest.mark.asyncio
async def test_dev_login_succeeds_in_dev_mode(client, test_db, test_user):
    """Test dev login endpoint works in dev mode."""
    with patch.object(settings, "DEV_MODE", True):
        response = client.post(
            "/api/auth/dev-login",
            json={"email": test_user.email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user.email

        # Verify last_login was updated
        await test_db.refresh(test_user)
        assert test_user.last_login is not None


def test_dev_login_blocked_in_production(client):
    """Test dev login endpoint is blocked in production mode."""
    with patch.object(settings, "DEV_MODE", False):
        response = client.post(
            "/api/auth/dev-login",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 404
        assert "Not available in production" in response.json()["detail"]


def test_dev_login_fails_with_nonexistent_user(client):
    """Test dev login fails when user doesn't exist."""
    with patch.object(settings, "DEV_MODE", True):
        response = client.post(
            "/api/auth/dev-login",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
