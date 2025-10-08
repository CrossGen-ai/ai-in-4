"""Tests for Stripe MCP integration service with mocked responses."""
import pytest
import hashlib
import hmac
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any

from services.stripe_service import StripeService, stripe_service
from core.config import settings


# Test data fixtures
@pytest.fixture
def valid_checkout_data() -> Dict[str, str]:
    """Valid checkout session input data."""
    return {
        "price_id": "price_1234567890",
        "user_email": "test@example.com",
        "referrer_code": "REF123"
    }


@pytest.fixture
def valid_webhook_payload() -> bytes:
    """Valid webhook payload."""
    return b'{"id": "evt_test_webhook", "object": "event"}'


@pytest.fixture
def valid_webhook_signature(valid_webhook_payload: bytes) -> str:
    """Generate valid webhook signature for testing."""
    timestamp = "1234567890"
    signed_payload = f"{timestamp}.{valid_webhook_payload.decode('utf-8')}"
    signature = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.fixture
def stripe_service_instance() -> StripeService:
    """Create fresh StripeService instance for testing."""
    return StripeService()


# Happy Path Tests

@pytest.mark.asyncio
async def test_create_checkout_session_with_valid_data(
    stripe_service_instance: StripeService,
    valid_checkout_data: Dict[str, str]
):
    """Test create_checkout_session with valid price_id and user_email."""
    # Arrange
    price_id = valid_checkout_data["price_id"]
    user_email = valid_checkout_data["user_email"]
    referrer_code = valid_checkout_data["referrer_code"]

    # Act
    result = await stripe_service_instance.create_checkout_session(
        price_id=price_id,
        user_email=user_email,
        referrer_code=referrer_code
    )

    # Assert
    assert result["price_id"] == price_id
    assert result["customer_id"] is not None
    assert result["metadata"]["user_email"] == user_email
    assert result["metadata"]["referrer_code"] == referrer_code
    assert "success_url" in result
    assert "cancel_url" in result
    assert settings.FRONTEND_URL in result["success_url"]
    assert settings.FRONTEND_URL in result["cancel_url"]


@pytest.mark.asyncio
async def test_create_checkout_session_without_referrer(
    stripe_service_instance: StripeService
):
    """Test create_checkout_session without referrer code."""
    # Arrange
    price_id = "price_test123"
    user_email = "noreferrer@example.com"

    # Act
    result = await stripe_service_instance.create_checkout_session(
        price_id=price_id,
        user_email=user_email
    )

    # Assert
    assert result["price_id"] == price_id
    assert result["metadata"]["user_email"] == user_email
    assert "referrer_code" not in result["metadata"]


def test_verify_webhook_signature_valid(
    stripe_service_instance: StripeService,
    valid_webhook_payload: bytes,
    valid_webhook_signature: str
):
    """Test verify_webhook_signature validates webhook events correctly."""
    # Act
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=valid_webhook_payload,
        signature=valid_webhook_signature
    )

    # Assert
    assert is_valid is True


@pytest.mark.asyncio
async def test_get_or_create_customer_generates_id(
    stripe_service_instance: StripeService
):
    """Test get_or_create_customer generates customer ID."""
    # Arrange
    email = "newcustomer@example.com"

    # Act
    customer_id = await stripe_service_instance.get_or_create_customer(email)

    # Assert
    assert customer_id is not None
    assert isinstance(customer_id, str)
    assert customer_id.startswith("cus_")
    # Verify email components are in ID (current placeholder logic)
    assert "newcustomer" in customer_id
    assert "example" in customer_id


@pytest.mark.asyncio
async def test_sync_products_returns_list(stripe_service_instance: StripeService):
    """Test sync_products fetches products list."""
    # Act
    products = await stripe_service_instance.sync_products()

    # Assert
    assert isinstance(products, list)


@pytest.mark.asyncio
async def test_sync_prices_returns_list(stripe_service_instance: StripeService):
    """Test sync_prices fetches prices list."""
    # Act
    prices = await stripe_service_instance.sync_prices()

    # Assert
    assert isinstance(prices, list)


@pytest.mark.asyncio
async def test_get_customer_payment_intents_returns_list(
    stripe_service_instance: StripeService
):
    """Test get_customer_payment_intents gets payment history."""
    # Arrange
    customer_id = "cus_test123"

    # Act
    payment_intents = await stripe_service_instance.get_customer_payment_intents(
        customer_id
    )

    # Assert
    assert isinstance(payment_intents, list)


@pytest.mark.asyncio
async def test_create_refund_full_amount(stripe_service_instance: StripeService):
    """Test create_refund creates full refund."""
    # Arrange
    payment_intent_id = "pi_test123"

    # Act
    refund = await stripe_service_instance.create_refund(payment_intent_id)

    # Assert
    assert refund["id"] is not None
    assert refund["status"] == "succeeded"
    assert refund["amount"] is None  # Full refund


@pytest.mark.asyncio
async def test_create_refund_partial_amount(stripe_service_instance: StripeService):
    """Test create_refund creates partial refund."""
    # Arrange
    payment_intent_id = "pi_test123"
    refund_amount = 500  # $5.00 in cents

    # Act
    refund = await stripe_service_instance.create_refund(
        payment_intent_id,
        amount=refund_amount
    )

    # Assert
    assert refund["id"] is not None
    assert refund["status"] == "succeeded"
    assert refund["amount"] == refund_amount


# Edge Case Tests

@pytest.mark.asyncio
async def test_get_or_create_customer_special_chars_in_email(
    stripe_service_instance: StripeService
):
    """Test customer creation with special characters in email."""
    # Arrange
    email = "user+tag@example.co.uk"

    # Act
    customer_id = await stripe_service_instance.get_or_create_customer(email)

    # Assert
    assert customer_id is not None
    assert customer_id.startswith("cus_")


def test_verify_webhook_signature_invalid_signature(
    stripe_service_instance: StripeService,
    valid_webhook_payload: bytes
):
    """Test webhook signature validation with invalid signature."""
    # Arrange
    invalid_signature = "t=1234567890,v1=invalidsignature123"

    # Act
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=valid_webhook_payload,
        signature=invalid_signature
    )

    # Assert
    assert is_valid is False


def test_verify_webhook_signature_missing_timestamp(
    stripe_service_instance: StripeService,
    valid_webhook_payload: bytes
):
    """Test webhook signature validation with missing timestamp."""
    # Arrange
    # Signature without timestamp
    signature = "v1=somesignature"

    # Act
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=valid_webhook_payload,
        signature=signature
    )

    # Assert
    assert is_valid is False


def test_verify_webhook_signature_missing_signature(
    stripe_service_instance: StripeService,
    valid_webhook_payload: bytes
):
    """Test webhook signature validation with missing signature."""
    # Arrange
    # Timestamp only, no signature
    signature = "t=1234567890"

    # Act
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=valid_webhook_payload,
        signature=signature
    )

    # Assert
    assert is_valid is False


def test_verify_webhook_signature_malformed_header(
    stripe_service_instance: StripeService,
    valid_webhook_payload: bytes
):
    """Test webhook signature validation with malformed header."""
    # Arrange
    malformed_signature = "not,a,valid=format"

    # Act
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=valid_webhook_payload,
        signature=malformed_signature
    )

    # Assert
    assert is_valid is False


def test_verify_webhook_signature_empty_string(
    stripe_service_instance: StripeService,
    valid_webhook_payload: bytes
):
    """Test webhook signature validation with empty signature."""
    # Arrange
    empty_signature = ""

    # Act
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=valid_webhook_payload,
        signature=empty_signature
    )

    # Assert
    assert is_valid is False


def test_verify_webhook_signature_handles_exceptions(
    stripe_service_instance: StripeService
):
    """Test webhook signature validation handles exceptions gracefully."""
    # Arrange
    # Pass invalid payload type to trigger exception
    invalid_payload = None
    signature = "t=123,v1=abc"

    # Act & Assert - should return False, not raise exception
    is_valid = stripe_service_instance.verify_webhook_signature(
        payload=invalid_payload,
        signature=signature
    )
    assert is_valid is False


# Configuration and Initialization Tests

def test_stripe_service_initialization_test_mode():
    """Test StripeService initializes correctly in test mode."""
    # Act
    service = StripeService()

    # Assert
    assert service.secret_key == settings.STRIPE_SECRET_KEY
    assert service.webhook_secret == settings.STRIPE_WEBHOOK_SECRET
    assert service.test_mode == settings.STRIPE_TEST_MODE


def test_stripe_service_initialization_validates_test_key():
    """Test StripeService validates test mode matches key type."""
    # Arrange - temporarily modify settings
    with patch.object(settings, 'STRIPE_TEST_MODE', True):
        with patch.object(settings, 'STRIPE_SECRET_KEY', 'sk_live_fakekeyforthistest'):
            # Act & Assert
            with pytest.raises(ValueError, match="STRIPE_TEST_MODE is True but secret key is not a test key"):
                StripeService()


def test_stripe_service_global_instance():
    """Test global stripe_service instance exists."""
    # Assert
    assert stripe_service is not None
    assert isinstance(stripe_service, StripeService)


# Idempotency Tests (Future MCP Integration)

@pytest.mark.asyncio
async def test_get_or_create_customer_idempotent(
    stripe_service_instance: StripeService
):
    """Test get_or_create_customer is idempotent for same email."""
    # Arrange
    email = "idempotent@example.com"

    # Act - call twice with same email
    customer_id_1 = await stripe_service_instance.get_or_create_customer(email)
    customer_id_2 = await stripe_service_instance.get_or_create_customer(email)

    # Assert - should return same ID (current placeholder logic)
    assert customer_id_1 == customer_id_2


# Empty/Null Input Tests

@pytest.mark.asyncio
async def test_create_checkout_session_empty_email(
    stripe_service_instance: StripeService
):
    """Test create_checkout_session with empty email."""
    # Act
    result = await stripe_service_instance.create_checkout_session(
        price_id="price_123",
        user_email=""
    )

    # Assert - current implementation doesn't validate, but returns data
    assert result["metadata"]["user_email"] == ""


@pytest.mark.asyncio
async def test_get_customer_payment_intents_empty_customer_id(
    stripe_service_instance: StripeService
):
    """Test get_customer_payment_intents with empty customer ID."""
    # Act
    payment_intents = await stripe_service_instance.get_customer_payment_intents("")

    # Assert - returns empty list (placeholder behavior)
    assert isinstance(payment_intents, list)


@pytest.mark.asyncio
async def test_create_refund_zero_amount(stripe_service_instance: StripeService):
    """Test create_refund with zero amount."""
    # Arrange
    payment_intent_id = "pi_test123"
    zero_amount = 0

    # Act
    refund = await stripe_service_instance.create_refund(
        payment_intent_id,
        amount=zero_amount
    )

    # Assert
    assert refund["amount"] == 0


# Integration Readiness Tests (Placeholder Verification)

@pytest.mark.asyncio
async def test_sync_products_placeholder_returns_empty_list(
    stripe_service_instance: StripeService
):
    """Verify sync_products returns empty list (placeholder implementation)."""
    # Act
    products = await stripe_service_instance.sync_products()

    # Assert - current placeholder returns []
    assert products == []


@pytest.mark.asyncio
async def test_sync_prices_placeholder_returns_empty_list(
    stripe_service_instance: StripeService
):
    """Verify sync_prices returns empty list (placeholder implementation)."""
    # Act
    prices = await stripe_service_instance.sync_prices()

    # Assert - current placeholder returns []
    assert prices == []


@pytest.mark.asyncio
async def test_get_customer_payment_intents_placeholder_returns_empty_list(
    stripe_service_instance: StripeService
):
    """Verify get_customer_payment_intents returns empty list (placeholder)."""
    # Act
    payment_intents = await stripe_service_instance.get_customer_payment_intents(
        "cus_test"
    )

    # Assert - current placeholder returns []
    assert payment_intents == []
