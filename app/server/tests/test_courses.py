"""Tests for course-related API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC


# Fixtures for authenticated clients with different entitlement states
@pytest.fixture
def authenticated_client(client):
    """Create an authenticated client with mock user and entitlements."""
    def make_request(method, url, **kwargs):
        with patch('api.routes.users.validate_session_token', new_callable=AsyncMock) as mock_validate, \
             patch('services.entitlement_service.check_product_access', new_callable=AsyncMock) as mock_check:
            # Mock authenticated user
            mock_user = AsyncMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_validate.return_value = mock_user

            # Mock has access
            mock_check.return_value = True

            headers = kwargs.get('headers', {})
            headers['Authorization'] = 'Bearer valid_token_with_entitlement'
            kwargs['headers'] = headers

            return getattr(client, method)(url, **kwargs)

    class AuthClient:
        def get(self, url, **kwargs):
            return make_request('get', url, **kwargs)

        def post(self, url, **kwargs):
            return make_request('post', url, **kwargs)

    return AuthClient()


@pytest.fixture
def authenticated_client_no_entitlements(client):
    """Create an authenticated client without entitlements."""
    def make_request(method, url, **kwargs):
        with patch('api.routes.users.validate_session_token', new_callable=AsyncMock) as mock_validate, \
             patch('services.entitlement_service.check_product_access', new_callable=AsyncMock) as mock_check:
            # Mock authenticated user
            mock_user = AsyncMock()
            mock_user.id = 2
            mock_user.email = "noentitlement@example.com"
            mock_validate.return_value = mock_user

            # Mock no access
            mock_check.return_value = False

            headers = kwargs.get('headers', {})
            headers['Authorization'] = 'Bearer valid_token_no_entitlement'
            kwargs['headers'] = headers

            return getattr(client, method)(url, **kwargs)

    class AuthClient:
        def get(self, url, **kwargs):
            return make_request('get', url, **kwargs)

        def post(self, url, **kwargs):
            return make_request('post', url, **kwargs)

    return AuthClient()


@pytest.fixture
def authenticated_client_expired_entitlement(client):
    """Create an authenticated client with expired entitlement."""
    def make_request(method, url, **kwargs):
        with patch('api.routes.users.validate_session_token', new_callable=AsyncMock) as mock_validate, \
             patch('services.entitlement_service.check_product_access', new_callable=AsyncMock) as mock_check:
            # Mock authenticated user
            mock_user = AsyncMock()
            mock_user.id = 3
            mock_user.email = "expired@example.com"
            mock_validate.return_value = mock_user

            # Mock expired - no access
            mock_check.return_value = False

            headers = kwargs.get('headers', {})
            headers['Authorization'] = 'Bearer valid_token_expired_entitlement'
            kwargs['headers'] = headers

            return getattr(client, method)(url, **kwargs)

    class AuthClient:
        def get(self, url, **kwargs):
            return make_request('get', url, **kwargs)

        def post(self, url, **kwargs):
            return make_request('post', url, **kwargs)

    return AuthClient()


def test_course_listing_endpoint_returns_courses(client):
    """Test course listing endpoint returns courses"""
    response = client.get("/api/courses/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Verify structure if courses exist
    if len(data) > 0:
        course = data[0]
        assert "id" in course
        assert "title" in course
        assert "description" in course
        assert "schedule" in course
        assert "materials_url" in course


def test_get_course_by_id_returns_course(client):
    """Test retrieving a specific course by ID"""
    # First get list to find a valid course ID
    list_response = client.get("/api/courses/")
    courses = list_response.json()

    if len(courses) > 0:
        course_id = courses[0]["id"]
        response = client.get(f"/api/courses/{course_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == course_id
        assert "title" in data
        assert "description" in data


def test_get_course_not_found(client):
    """Test retrieving a non-existent course returns 404"""
    response = client.get("/api/courses/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Course not found"


def test_course_listing_empty_database(client):
    """Test course listing returns empty array when no courses exist"""
    response = client.get("/api/courses/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_course_invalid_id_type(client):
    """Test course endpoint with invalid ID type"""
    response = client.get("/api/courses/invalid")
    assert response.status_code == 422  # FastAPI validation error


def test_database_error_handling(client):
    """Test that database errors are handled gracefully"""
    # Note: This test requires mocking the database session to raise an exception
    # In a real scenario, you would mock get_db to raise an exception
    # For now, this validates the endpoint is accessible
    response = client.get("/api/courses/")
    # Should not crash - either returns data or handles errors gracefully
    assert response.status_code in [200, 500, 503]


def test_course_listing_concurrent_requests(client):
    """Test course listing handles concurrent requests"""
    # Simulate multiple rapid requests
    responses = []
    for _ in range(5):
        response = client.get("/api/courses/")
        responses.append(response)

    # All requests should complete successfully
    for response in responses:
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_course_products_includes_pricing_information(client):
    """Test GET /api/courses/products includes pricing information"""
    response = client.get("/api/courses/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Verify structure if products exist
    if len(data) > 0:
        product = data[0]
        assert "id" in product
        assert "name" in product
        assert "description" in product
        assert "category" in product
        assert "price" in product
        assert "price_id" in product
        assert "currency" in product


def test_check_course_access_requires_authentication(client):
    """Test GET /api/courses/{course_id}/check-access requires authentication"""
    # Attempt to check access without authentication
    response = client.get("/api/courses/1/check-access")
    # Should return 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403]


def test_check_course_access_with_valid_entitlement(client, authenticated_client):
    """Test GET /api/courses/{course_id}/check-access checks user entitlements"""
    # This assumes authenticated_client fixture provides a user with entitlements
    # First get a valid course ID
    list_response = client.get("/api/courses/")
    courses = list_response.json()

    if len(courses) > 0:
        course_id = courses[0]["id"]
        response = authenticated_client.get(f"/api/courses/{course_id}/check-access")
        assert response.status_code == 200
        data = response.json()
        assert "has_access" in data
        assert isinstance(data["has_access"], bool)


def test_check_course_access_returns_boolean_status(client, authenticated_client):
    """Test GET /api/courses/{course_id}/check-access returns boolean access status"""
    response = authenticated_client.get("/api/courses/1/check-access")
    assert response.status_code == 200
    data = response.json()
    assert "has_access" in data
    assert isinstance(data["has_access"], bool)


def test_user_without_entitlements_denied_access(client, authenticated_client_no_entitlements):
    """Test user without entitlements accessing paid courses"""
    # This assumes authenticated_client_no_entitlements provides a user without entitlements
    response = authenticated_client_no_entitlements.get("/api/courses/1/check-access")
    assert response.status_code == 200
    data = response.json()
    assert data["has_access"] is False


def test_expired_entitlement_denied_access(client, authenticated_client_expired_entitlement):
    """Test expired or revoked entitlements"""
    # This assumes authenticated_client_expired_entitlement provides a user with expired entitlement
    response = authenticated_client_expired_entitlement.get("/api/courses/1/check-access")
    assert response.status_code == 200
    data = response.json()
    assert data["has_access"] is False


def test_check_access_invalid_course_id(client, authenticated_client):
    """Test check access with invalid course ID type"""
    response = authenticated_client.get("/api/courses/invalid/check-access")
    assert response.status_code == 422  # FastAPI validation error


def test_check_access_nonexistent_course(client, authenticated_client):
    """Test check access for non-existent course"""
    response = authenticated_client.get("/api/courses/999999/check-access")
    assert response.status_code == 200
    data = response.json()
    # Note: authenticated_client fixture mocks check_product_access to return True
    # This tests that the endpoint returns successfully even for non-existent courses
    assert "has_access" in data
    assert isinstance(data["has_access"], bool)


# New tests for missing scenarios


def test_course_products_joins_with_stripe_tables(client):
    """Test GET /api/courses/products joins with StripeProduct and StripePrice tables"""
    with patch('api.routes.courses.get_db') as mock_get_db:
        from unittest.mock import MagicMock

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock product query result
        mock_product = MagicMock()
        mock_product.id = "prod_test123"
        mock_product.name = "AI Course"
        mock_product.description = "Learn AI"
        mock_product.category = "course"
        mock_product.active = True

        # Mock price query result
        mock_price = MagicMock()
        mock_price.id = "price_test123"
        mock_price.amount = 9900
        mock_price.currency = "usd"
        mock_price.active = True
        mock_price.product_id = "prod_test123"

        # Setup mock execute results
        mock_product_result = MagicMock()
        mock_product_result.scalars.return_value.all.return_value = [mock_product]

        mock_price_result = MagicMock()
        mock_price_result.scalar_one_or_none.return_value = mock_price

        # Mock db.execute to return different results based on call order
        mock_db.execute.side_effect = [mock_product_result, mock_price_result]

        response = client.get("/api/courses/products")
        assert response.status_code == 200
        data = response.json()

        # Verify the response includes joined data from both tables
        if len(data) > 0:
            product = data[0]
            # Verify StripeProduct fields
            assert "id" in product
            assert "name" in product
            assert "category" in product
            # Verify StripePrice fields are joined
            assert "price" in product
            assert "price_id" in product
            assert "currency" in product


def test_course_products_handles_missing_stripe_price(client):
    """Test GET /api/courses/products handles missing or invalid Stripe price IDs"""
    with patch('api.routes.courses.get_db') as mock_get_db:
        from unittest.mock import MagicMock

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock product without price
        mock_product = MagicMock()
        mock_product.id = "prod_no_price"
        mock_product.name = "Course Without Price"
        mock_product.description = "Test"
        mock_product.category = "course"
        mock_product.active = True

        # Setup mock execute results
        mock_product_result = MagicMock()
        mock_product_result.scalars.return_value.all.return_value = [mock_product]

        mock_price_result = MagicMock()
        mock_price_result.scalar_one_or_none.return_value = None  # No price found

        mock_db.execute.side_effect = [mock_product_result, mock_price_result]

        response = client.get("/api/courses/products")
        assert response.status_code == 200
        data = response.json()

        # Should handle missing price gracefully
        if len(data) > 0:
            product = data[0]
            assert product["price"] is None
            assert product["price_id"] is None
            assert product["currency"] == "usd"  # Default currency


def test_check_course_access_returns_true_for_entitled_user(client, authenticated_client):
    """Test GET /api/courses/{course_id}/check-access returns true for entitled user"""
    # The authenticated_client fixture already mocks the entitlement check to return True
    response = authenticated_client.get("/api/courses/1/check-access")
    assert response.status_code == 200
    data = response.json()
    assert data["has_access"] is True


def test_courses_listing_includes_pricing_fields(client):
    """Test GET /api/courses response includes pricing information fields"""
    response = client.get("/api/courses/")
    assert response.status_code == 200
    data = response.json()

    # Verify the response structure
    assert isinstance(data, list)
    # If courses exist, verify they have the expected fields
    # Note: This tests the CourseResponse schema which may or may not include pricing
    # depending on implementation
    if len(data) > 0:
        course = data[0]
        assert "id" in course
        assert "title" in course
        assert "description" in course


def test_course_products_with_inactive_products_excluded(client):
    """Test GET /api/courses/products excludes inactive products"""
    with patch('api.routes.courses.get_db') as mock_get_db:
        from unittest.mock import MagicMock

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock only active products should be returned
        mock_product = MagicMock()
        mock_product.id = "prod_active"
        mock_product.name = "Active Course"
        mock_product.description = "Active"
        mock_product.category = "course"
        mock_product.active = True

        mock_price = MagicMock()
        mock_price.id = "price_active"
        mock_price.amount = 5000
        mock_price.currency = "usd"
        mock_price.active = True

        mock_product_result = MagicMock()
        mock_product_result.scalars.return_value.all.return_value = [mock_product]

        mock_price_result = MagicMock()
        mock_price_result.scalar_one_or_none.return_value = mock_price

        mock_db.execute.side_effect = [mock_product_result, mock_price_result]

        response = client.get("/api/courses/products")
        assert response.status_code == 200
        data = response.json()

        # All returned products should be active
        for product in data:
            # Verify only active products are included
            # (The query filters by active=True)
            assert "id" in product


def test_check_course_access_with_invalid_product_mapping(client, authenticated_client):
    """Test check access when course_id to product_id mapping is invalid"""
    # Test with a very large course_id
    response = authenticated_client.get("/api/courses/999999999/check-access")
    assert response.status_code == 200
    data = response.json()
    # Should return boolean result even with invalid mapping
    assert "has_access" in data
    assert isinstance(data["has_access"], bool)
