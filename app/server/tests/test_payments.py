"""Tests for payment routes using TestClient and mocked services."""
import pytest
from unittest.mock import patch, AsyncMock, ANY, MagicMock
from datetime import datetime, UTC
from sqlalchemy import select

from main import app
from db.models import StripeProduct, StripePrice, Entitlement, User, UserExperience
from api.routes.users import get_current_user


# Valid test data matching the schema
VALID_CHECKOUT_REQUEST = {
    "product_id": "prod_test_123",
    "referrer_code": None,
}


@pytest.fixture
def override_get_current_user(test_user):
    """Override get_current_user dependency for authenticated tests."""
    async def _get_current_user_override():
        return test_user

    # Store original to restore later
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _get_current_user_override
    yield test_user
    # Restore original or remove override
    if original:
        app.dependency_overrides[get_current_user] = original
    else:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_checkout_creates_session_with_valid_auth(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout creates checkout session with employment-based pricing."""
    # Get or create user experience with employment status
    experience_result = await test_db.execute(
        select(UserExperience).where(UserExperience.user_id == override_get_current_user.id)
    )
    user_experience = experience_result.scalar_one_or_none()

    if user_experience:
        # Update existing
        user_experience.employment_status = "Employed full-time"
        user_experience.name = "Test User"
    else:
        # Create new
        user_experience = UserExperience(
            user_id=override_get_current_user.id,
            employment_status="Employed full-time",
            name="Test User",
        )
        test_db.add(user_experience)

    await test_db.flush()

    # Create test product and price with employment eligibility
    product = StripeProduct(
        id="prod_test_123",
        name="Test Product",
        description="Test product description",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_test_123",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Test Price - Employed",
            "eligible_employment_statuses": ["Employed full-time", "Employed part-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Mock Stripe checkout session creation
    mock_session = MagicMock()
    mock_session.id = "cs_test_mock_123"
    mock_session.url = "https://checkout.stripe.com/test/cs_test_mock_123"

    with patch("api.routes.payments.stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        response = client.post(
            "/api/payments/checkout",
            json=VALID_CHECKOUT_REQUEST,
        )

        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["session_id"] == "cs_test_mock_123"
        assert data["checkout_url"] == "https://checkout.stripe.com/test/cs_test_mock_123"

        # Verify Stripe was called with correct parameters
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["line_items"][0]["price"] == "price_test_123"
        assert call_args.kwargs["metadata"]["price_id"] == "price_test_123"

        # Verify payment_intent_data is passed with metadata
        assert "payment_intent_data" in call_args.kwargs
        assert "metadata" in call_args.kwargs["payment_intent_data"]
        payment_intent_metadata = call_args.kwargs["payment_intent_data"]["metadata"]
        assert payment_intent_metadata["user_id"] == str(override_get_current_user.id)
        assert payment_intent_metadata["price_id"] == "price_test_123"
        assert payment_intent_metadata["user_email"] == override_get_current_user.email


@pytest.mark.asyncio
async def test_checkout_validates_product_exists(client, override_get_current_user):
    """Test POST /api/payments/checkout validates product exists."""
    # Request with non-existent product
    response = client.post(
        "/api/payments/checkout",
        json={"product_id": "prod_nonexistent", "referrer_code": None},
    )

    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_selects_price_based_on_employment_status(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout selects correct price based on employment status."""
    # Create product with two prices: employed and student rates
    product = StripeProduct(
        id="prod_employment_test",
        name="Test Course",
        category="curriculum",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    employed_price = StripePrice(
        id="price_employed",
        product_id=product.id,
        amount=49700,  # $497
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Employed Rate",
            "eligible_employment_statuses": ["Employed full-time", "Employed part-time", "Self-employed/Freelancer"]
        }
    )
    student_price = StripePrice(
        id="price_student",
        product_id=product.id,
        amount=9700,  # $97
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Student Rate",
            "eligible_employment_statuses": ["Student", "Between jobs", "Other"]
        }
    )
    test_db.add(employed_price)
    test_db.add(student_price)
    await test_db.commit()

    # Test 1: User with "Employed full-time" status should get employed price
    experience_result = await test_db.execute(
        select(UserExperience).where(UserExperience.user_id == override_get_current_user.id)
    )
    user_experience = experience_result.scalar_one_or_none()
    if user_experience:
        user_experience.employment_status = "Employed full-time"
    else:
        user_experience = UserExperience(
            user_id=override_get_current_user.id,
            employment_status="Employed full-time",
            name="Test User",
        )
        test_db.add(user_experience)
    await test_db.commit()

    mock_session_employed = MagicMock()
    mock_session_employed.id = "cs_employed_123"
    mock_session_employed.url = "https://checkout.stripe.com/employed"

    with patch("api.routes.payments.stripe.checkout.Session.create", return_value=mock_session_employed) as mock_create:
        response = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_employment_test", "referrer_code": None},
        )

        assert response.status_code == 200
        # Verify employed price was selected
        call_args = mock_create.call_args
        assert call_args.kwargs["line_items"][0]["price"] == "price_employed"

    # Test 2: Change to "Student" status should get student price
    user_experience.employment_status = "Student"
    await test_db.commit()

    mock_session_student = MagicMock()
    mock_session_student.id = "cs_student_123"
    mock_session_student.url = "https://checkout.stripe.com/student"

    with patch("api.routes.payments.stripe.checkout.Session.create", return_value=mock_session_student) as mock_create:
        response = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_employment_test", "referrer_code": None},
        )

        assert response.status_code == 200
        # Verify student price was selected
        call_args = mock_create.call_args
        assert call_args.kwargs["line_items"][0]["price"] == "price_student"


@pytest.mark.asyncio
async def test_checkout_rejects_invalid_employment_status(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout rejects invalid employment status."""
    # Create product with employment-based pricing
    product = StripeProduct(
        id="prod_invalid_emp_test",
        name="Test Course",
        category="curriculum",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    # Create prices with valid employment status metadata
    employed_price = StripePrice(
        id="price_employed_invalid_test",
        product_id=product.id,
        amount=49700,
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Employed Rate",
            "eligible_employment_statuses": ["Employed full-time", "Employed part-time"]
        }
    )
    student_price = StripePrice(
        id="price_student_invalid_test",
        product_id=product.id,
        amount=9700,
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Student Rate",
            "eligible_employment_statuses": ["Student", "Between jobs"]
        }
    )
    test_db.add(employed_price)
    test_db.add(student_price)
    await test_db.commit()

    # Set user employment status to INVALID value
    experience_result = await test_db.execute(
        select(UserExperience).where(UserExperience.user_id == override_get_current_user.id)
    )
    user_experience = experience_result.scalar_one_or_none()
    if user_experience:
        user_experience.employment_status = "GARBAGE_INVALID_STATUS_123"
    else:
        user_experience = UserExperience(
            user_id=override_get_current_user.id,
            employment_status="GARBAGE_INVALID_STATUS_123",
            name="Test User",
        )
        test_db.add(user_experience)
    await test_db.commit()

    # Attempt checkout
    response = client.post(
        "/api/payments/checkout",
        json={"product_id": "prod_invalid_emp_test", "referrer_code": None},
    )

    # Should return 400 error
    assert response.status_code == 400
    assert "No price available for employment status" in response.json()["detail"]
    assert "GARBAGE_INVALID_STATUS_123" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_rejects_empty_employment_status(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout rejects empty string employment status."""
    # Create product and prices
    product = StripeProduct(
        id="prod_empty_emp_test",
        name="Test Course",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_empty_emp_test",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Set employment status to empty string
    experience_result = await test_db.execute(
        select(UserExperience).where(UserExperience.user_id == override_get_current_user.id)
    )
    user_experience = experience_result.scalar_one_or_none()
    if user_experience:
        user_experience.employment_status = ""  # Empty string
    else:
        user_experience = UserExperience(
            user_id=override_get_current_user.id,
            employment_status="",
            name="Test User",
        )
        test_db.add(user_experience)
    await test_db.commit()

    # Attempt checkout
    response = client.post(
        "/api/payments/checkout",
        json={"product_id": "prod_empty_emp_test", "referrer_code": None},
    )

    # Should return 400 error
    assert response.status_code == 400
    # Empty string is treated as missing employment status
    assert "employment status not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_checkout_validates_referrer_code_if_provided(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout validates referrer code if provided."""
    # Create product and price
    product = StripeProduct(
        id="prod_test_456",
        name="Test Product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_test_456",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student", "Employed full-time", "Employed part-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Mock referral_service.validate_referral_code to return None (invalid code)
    with patch("api.routes.payments.referral_service.validate_referral_code", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None

        response = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_test_456", "referrer_code": "INVALID123"},
        )

        assert response.status_code == 400
        assert "Invalid referrer code" in response.json()["detail"]
        mock_validate.assert_called_once()


@pytest.mark.asyncio
async def test_checkout_prevents_self_referral(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout prevents self-referral."""
    # Create product and price
    product = StripeProduct(
        id="prod_test_789",
        name="Test Product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="prod_test_789",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student", "Employed full-time", "Employed part-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Mock referral_service to return the same user (self-referral)
    with patch("api.routes.payments.referral_service.validate_referral_code", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = override_get_current_user

        response = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_test_789", "referrer_code": "SELF123"},
        )

        assert response.status_code == 400
        assert "Cannot use your own referral code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_includes_referrer_in_metadata(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout includes referrer in metadata when valid."""
    # Create referrer user
    referrer = User(
        email="referrer@example.com",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    test_db.add(referrer)
    await test_db.flush()

    # Create product and price
    product = StripeProduct(
        id="prod_test_ref",
        name="Test Product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_test_ref",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student", "Employed full-time", "Employed part-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Mock Stripe checkout session creation
    mock_session = MagicMock()
    mock_session.id = "cs_test_ref_123"
    mock_session.url = "https://checkout.stripe.com/test/cs_test_ref_123"

    # Mock referral_service to return referrer user
    with patch("api.routes.payments.referral_service.validate_referral_code", new_callable=AsyncMock) as mock_validate, \
         patch("api.routes.payments.stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        mock_validate.return_value = referrer

        response = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_test_ref", "referrer_code": "VALID123"},
        )

        assert response.status_code == 200

        # Verify payment_intent_data includes referrer information
        call_args = mock_create.call_args
        assert "payment_intent_data" in call_args.kwargs
        payment_intent_metadata = call_args.kwargs["payment_intent_data"]["metadata"]
        assert payment_intent_metadata["referrer_id"] == str(referrer.id)
        assert payment_intent_metadata["referrer_code"] == "VALID123"


def test_webhook_handles_payment_intent_succeeded_event(client):
    """Test POST /api/payments/webhook handles payment_intent.succeeded event."""
    # Mock services
    with patch("api.routes.payments.entitlement_service.grant_entitlement", new_callable=AsyncMock) as mock_grant:
        mock_grant.return_value = None

        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "amount": 1000,
                    "metadata": {
                        "user_id": "1",
                        "price_id": "price_test_123",
                        "user_email": "test@example.com",
                    }
                }
            }
        }

        response = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_grant.assert_called_once_with(
            user_id=1,
            price_id="price_test_123",
            payment_intent_id="pi_test_123",
            db=ANY,
        )


def test_webhook_validates_json_payload(client):
    """Test POST /api/payments/webhook validates JSON payload."""
    response = client.post(
        "/api/payments/webhook",
        data="invalid json",
        headers={"stripe-signature": "test_signature", "content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]


def test_webhook_handles_missing_metadata(client):
    """Test POST /api/payments/webhook handles missing metadata gracefully."""
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_missing_metadata",
                "metadata": {}  # Missing required fields
            }
        }
    }

    response = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Missing metadata" in data["message"]


def test_webhook_grants_entitlements(client):
    """Test POST /api/payments/webhook grants entitlements."""
    with patch("api.routes.payments.entitlement_service.grant_entitlement", new_callable=AsyncMock) as mock_grant:
        mock_grant.return_value = None

        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_entitlement",
                    "amount": 2000,
                    "metadata": {
                        "user_id": "5",
                        "price_id": "price_premium",
                        "user_email": "premium@example.com",
                    }
                }
            }
        }

        response = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200
        mock_grant.assert_called_once()


def test_webhook_processes_referrals(client):
    """Test POST /api/payments/webhook processes referrals."""
    with patch("api.routes.payments.entitlement_service.grant_entitlement", new_callable=AsyncMock) as mock_grant:
        with patch("api.routes.payments.referral_service.create_referral", new_callable=AsyncMock) as mock_create_ref:
            with patch("api.routes.payments.referral_service.apply_referral_credit", new_callable=AsyncMock) as mock_apply_credit:
                # Mock referral creation
                mock_referral = AsyncMock()
                mock_referral.id = 1
                mock_create_ref.return_value = mock_referral

                webhook_payload = {
                    "type": "payment_intent.succeeded",
                    "data": {
                        "object": {
                            "id": "pi_test_referral",
                            "amount": 4000,
                            "metadata": {
                                "user_id": "10",
                                "price_id": "price_test_referral",
                                "user_email": "referred@example.com",
                                "referrer_id": "3",
                            }
                        }
                    }
                }

                response = client.post(
                    "/api/payments/webhook",
                    json=webhook_payload,
                    headers={"stripe-signature": "test_signature"},
                )

                assert response.status_code == 200
                mock_grant.assert_called_once()
                mock_create_ref.assert_called_once()
                mock_apply_credit.assert_called_once()

                # Verify credit calculation (25% of amount)
                call_args = mock_apply_credit.call_args
                assert call_args.kwargs["amount"] == 1000  # 25% of 4000


def test_webhook_handles_entitlement_error(client):
    """Test POST /api/payments/webhook handles entitlement errors."""
    with patch("api.routes.payments.entitlement_service.grant_entitlement", new_callable=AsyncMock) as mock_grant:
        mock_grant.side_effect = Exception("Database error")

        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_error",
                    "metadata": {
                        "user_id": "1",
                        "price_id": "price_test_123",
                    }
                }
            }
        }

        response = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Database error" in data["message"]


def test_webhook_handles_referral_error_gracefully(client):
    """Test POST /api/payments/webhook handles referral errors without failing."""
    with patch("api.routes.payments.entitlement_service.grant_entitlement", new_callable=AsyncMock) as mock_grant:
        with patch("api.routes.payments.referral_service.create_referral", new_callable=AsyncMock) as mock_create_ref:
            mock_create_ref.side_effect = Exception("Referral service error")

            webhook_payload = {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_test_ref_error",
                        "amount": 1000,
                        "metadata": {
                            "user_id": "1",
                            "price_id": "price_test_123",
                            "user_email": "test@example.com",
                            "referrer_id": "2",
                        }
                    }
                }
            }

            response = client.post(
                "/api/payments/webhook",
                json=webhook_payload,
                headers={"stripe-signature": "test_signature"},
            )

            # Should still succeed even if referral fails
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            mock_grant.assert_called_once()


def test_webhook_ignores_non_payment_intent_events(client):
    """Test POST /api/payments/webhook ignores non-payment_intent.succeeded events."""
    webhook_payload = {
        "type": "customer.created",
        "data": {
            "object": {
                "id": "cus_test_123",
            }
        }
    }

    response = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_get_entitlements_returns_user_entitlements(client, override_get_current_user, test_db):
    """Test GET /api/payments/entitlements returns user entitlements."""
    # Create product, price, and entitlement
    product = StripeProduct(
        id="prod_test_ent",
        name="Premium Course",
        description="Premium course access",
        category="curriculum",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_test_ent",
        product_id=product.id,
        amount=5000,
        currency="usd",
        active=True,
    )
    test_db.add(price)
    await test_db.flush()

    entitlement = Entitlement(
        user_id=override_get_current_user.id,
        stripe_price_id=price.id,
        stripe_payment_intent_id="pi_test_ent",
        status="active",
        created_at=datetime.now(UTC),
    )
    test_db.add(entitlement)
    await test_db.commit()

    response = client.get("/api/payments/entitlements")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["price_id"] == price.id
    assert data[0]["product_id"] == product.id
    assert data[0]["product_name"] == "Premium Course"
    assert data[0]["status"] == "active"


@pytest.mark.asyncio
async def test_get_entitlements_returns_empty_list_for_no_entitlements(client, override_get_current_user):
    """Test GET /api/payments/entitlements returns empty list when user has no entitlements."""
    response = client.get("/api/payments/entitlements")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_referral_stats_returns_user_referral_stats(client, override_get_current_user):
    """Test GET /api/payments/referrals returns user referral stats."""
    # Mock referral_service.get_referral_stats
    with patch("api.routes.payments.referral_service.get_referral_stats", new_callable=AsyncMock) as mock_stats:
        mock_stats.return_value = {
            "referral_code": "TEST123",
            "total_referrals": 5,
            "pending_referrals": 2,
            "total_credits": 1000,
        }

        response = client.get("/api/payments/referrals")

        assert response.status_code == 200
        data = response.json()
        assert data["referral_code"] == "TEST123"
        assert data["total_referrals"] == 5
        assert data["pending_referrals"] == 2
        assert data["total_credits"] == 1000
        mock_stats.assert_called_once_with(override_get_current_user.id, ANY)


@pytest.mark.asyncio
async def test_sync_products_returns_placeholder(client, override_get_current_user):
    """Test POST /api/payments/sync-products syncs products from Stripe."""
    response = client.post("/api/payments/sync-products")

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_checkout_handles_multiple_simultaneous_requests(client, override_get_current_user, test_db):
    """Test multiple simultaneous checkout requests for the same user."""
    # Create product and price
    product = StripeProduct(
        id="prod_test_multi",
        name="Test Product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_test_multi",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student", "Employed full-time", "Employed part-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Mock Stripe checkout session creation
    mock_session = MagicMock()
    mock_session.id = "cs_test_multi_123"
    mock_session.url = "https://checkout.stripe.com/test/cs_test_multi_123"

    with patch("api.routes.payments.stripe.checkout.Session.create", return_value=mock_session):
        # Make multiple requests
        response1 = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_test_multi", "referrer_code": None},
        )
        response2 = client.post(
            "/api/payments/checkout",
            json={"product_id": "prod_test_multi", "referrer_code": None},
        )

    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200

    # Both should return valid checkout URLs and session IDs
    data1 = response1.json()
    data2 = response2.json()
    assert "checkout_url" in data1
    assert "session_id" in data1
    assert "checkout_url" in data2
    assert "session_id" in data2
    # Note: Session IDs may be identical for same user/price in placeholder implementation
    # In production with real Stripe integration, each would be unique


def test_webhook_idempotency_for_duplicate_events(client):
    """Test POST /api/payments/webhook handles duplicate webhook events (idempotency)."""
    # This tests that the webhook can be called multiple times with the same event
    # Note: Actual idempotency would require checking if payment_intent_id already processed
    with patch("api.routes.payments.entitlement_service.grant_entitlement", new_callable=AsyncMock):
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_duplicate",
                    "amount": 1000,
                    "metadata": {
                        "user_id": "1",
                        "price_id": "price_test_123",
                        "user_email": "test@example.com",
                    }
                }
            }
        }

        # First webhook call
        response1 = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Second webhook call (duplicate)
        response2 = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Note: In production, grant_entitlement should handle idempotency
        # to prevent duplicate entitlements


@pytest.mark.asyncio
async def test_webhook_idempotency_creates_single_entitlement_in_database(
    client, override_get_current_user, test_db
):
    """
    Test webhook idempotency with actual database verification.

    Verifies that sending the same payment_intent.succeeded event twice
    results in only ONE entitlement in the database (not two).

    This is the REAL idempotency test - previous test used mocks.
    """
    # Arrange - create product and price
    product = StripeProduct(
        id="prod_idempotent_test",
        name="Idempotency Test Product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_idempotent_test",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student", "Employed full-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Webhook payload
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_idempotent_test_12345",  # Same ID for both calls
                "amount": 1000,
                "metadata": {
                    "user_id": str(override_get_current_user.id),
                    "price_id": "price_idempotent_test",
                    "user_email": override_get_current_user.email,
                }
            }
        }
    }

    # Act - send webhook TWICE with same payment_intent.id
    response1 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )

    response2 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )

    # Assert - both requests should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200

    # CRITICAL ASSERTION: Only ONE entitlement should exist in database
    result = await test_db.execute(
        select(Entitlement).where(
            Entitlement.stripe_payment_intent_id == "pi_idempotent_test_12345"
        )
    )
    entitlements = list(result.scalars().all())

    assert len(entitlements) == 1, (
        f"Expected exactly 1 entitlement, found {len(entitlements)}. "
        f"Idempotency failed - duplicate entitlement created!"
    )

    # Verify the single entitlement has correct data
    entitlement = entitlements[0]
    assert entitlement.user_id == override_get_current_user.id
    assert entitlement.stripe_price_id == "price_idempotent_test"
    assert entitlement.status == "active"
