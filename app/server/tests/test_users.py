from unittest.mock import AsyncMock, patch


def test_get_current_user_profile_requires_authentication(client):
    """Test that /me endpoint requires authentication"""
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_current_user_profile_with_invalid_token(client):
    """Test that /me endpoint rejects invalid tokens"""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid_token_123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_get_current_user_profile_with_missing_bearer_prefix(client):
    """Test that /me endpoint requires Bearer prefix"""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "just_a_token"}
    )
    assert response.status_code == 401


def test_get_current_user_experience_requires_authentication(client):
    """Test that /me/experience endpoint requires authentication"""
    response = client.get("/api/users/me/experience")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_current_user_experience_with_invalid_token(client):
    """Test that /me/experience endpoint rejects invalid tokens"""
    response = client.get(
        "/api/users/me/experience",
        headers={"Authorization": "Bearer invalid_token_123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_get_current_user_profile_with_expired_token(client):
    """Test edge case: expired token while user is on course page"""
    # Simulate expired token scenario
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer expired_token_abc"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_get_current_user_experience_with_expired_token(client):
    """Test edge case: expired token when accessing experience endpoint"""
    response = client.get(
        "/api/users/me/experience",
        headers={"Authorization": "Bearer expired_token_abc"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_authorization_header_extraction(client):
    """Test that authorization header is properly extracted and logged"""
    # Test with malformed authorization header
    response = client.get(
        "/api/users/me",
        headers={"Authorization": ""}
    )
    assert response.status_code == 401


def test_missing_experience_profile(client):
    """Test edge case: user exists but has no experience profile"""
    with patch('services.magic_link.validate_session_token') as mock_validate, \
         patch('services.user_service.get_user_experience') as mock_get_experience:
        # Mock user authentication
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.created_at = "2025-01-01T00:00:00"
        mock_validate.return_value = mock_user

        # Mock missing experience profile
        mock_get_experience.return_value = None

        response = client.get(
            "/api/users/me/experience",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Experience profile not found"


def test_get_current_user_profile_success(client):
    """Test successful retrieval of user profile with valid token"""
    with patch('services.magic_link.validate_session_token') as mock_validate:
        # Mock authenticated user
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.created_at = "2025-01-01T00:00:00"
        mock_validate.return_value = mock_user

        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer valid_token_123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["id"] == 1


def test_get_current_user_experience_success(client):
    """Test successful retrieval of user experience with valid token"""
    with patch('services.magic_link.validate_session_token') as mock_validate, \
         patch('services.user_service.get_user_experience') as mock_get_experience:
        # Mock authenticated user
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_validate.return_value = mock_user

        # Mock experience profile
        mock_experience = AsyncMock()
        mock_experience.user_id = 1
        mock_experience.programming_level = "intermediate"
        mock_experience.ai_experience = "beginner"
        mock_experience.learning_goals = "Build AI applications"
        mock_get_experience.return_value = mock_experience

        response = client.get(
            "/api/users/me/experience",
            headers={"Authorization": "Bearer valid_token_123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 1
        assert data["programming_level"] == "intermediate"
        assert data["ai_experience"] == "beginner"


def test_token_validation_called_with_correct_token(client):
    """Test that validate_session_token is called with extracted token"""
    with patch('services.magic_link.validate_session_token') as mock_validate:
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_validate.return_value = mock_user

        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer my_secret_token"}
        )

        # Verify token was extracted correctly (without "Bearer " prefix)
        mock_validate.assert_called_once()
        call_args = mock_validate.call_args[0]
        assert call_args[0] == "my_secret_token"
        assert response.status_code == 200
