"""Tests for Pydantic schema validation for payment-related schemas.

This module tests the validation logic of payment-related Pydantic schemas including:
- CheckoutSessionRequest
- CheckoutSessionResponse
- WebhookEvent
- EntitlementResponse
- ReferralResponse
- StripeProductResponse

Testing approach: Pure schema validation (no mocking required for Pydantic models).
"""
import pytest
from pydantic import ValidationError
from datetime import datetime, UTC

from models.schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    WebhookEvent,
    EntitlementResponse,
    ReferralResponse,
    StripeProductResponse,
)


class TestCheckoutSessionRequest:
    """Test CheckoutSessionRequest schema validation."""

    def test_valid_checkout_request_with_price_id(self):
        """Test valid checkout request with only product_id."""
        # Arrange & Act
        request = CheckoutSessionRequest(product_id="prod_123abc")

        # Assert
        assert request.product_id == "prod_123abc"
        assert request.referrer_code is None

    def test_valid_checkout_request_with_referrer_code(self):
        """Test valid checkout request with referrer code."""
        # Arrange & Act
        request = CheckoutSessionRequest(
            product_id="prod_123abc",
            referrer_code="REF123"
        )

        # Assert
        assert request.product_id == "prod_123abc"
        assert request.referrer_code == "REF123"

    def test_missing_price_id_raises_validation_error(self):
        """Test that missing product_id raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CheckoutSessionRequest(referrer_code="REF123")

        # Verify error mentions the missing field
        assert "product_id" in str(exc_info.value)

    def test_empty_price_id_accepted_by_schema(self):
        """Test that empty product_id is accepted by schema (no min_length constraint)."""
        # Note: Schema doesn't enforce min_length, validation happens in business logic
        # Arrange & Act
        request = CheckoutSessionRequest(product_id="")

        # Assert
        assert request.product_id == ""

    def test_invalid_referrer_code_type(self):
        """Test that invalid referrer_code type raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            CheckoutSessionRequest(
                product_id="prod_123abc",
                referrer_code=12345  # Should be string, not int
            )


class TestCheckoutSessionResponse:
    """Test CheckoutSessionResponse schema validation."""

    def test_valid_checkout_response(self):
        """Test valid checkout session response."""
        # Arrange & Act
        response = CheckoutSessionResponse(
            checkout_url="https://checkout.stripe.com/c/pay/cs_test_123",
            session_id="cs_test_123abc"
        )

        # Assert
        assert response.checkout_url == "https://checkout.stripe.com/c/pay/cs_test_123"
        assert response.session_id == "cs_test_123abc"

    def test_missing_checkout_url_raises_validation_error(self):
        """Test that missing checkout_url raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CheckoutSessionResponse(session_id="cs_test_123abc")

        assert "checkout_url" in str(exc_info.value)

    def test_missing_session_id_raises_validation_error(self):
        """Test that missing session_id raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CheckoutSessionResponse(
                checkout_url="https://checkout.stripe.com/c/pay/cs_test_123"
            )

        assert "session_id" in str(exc_info.value)

    def test_invalid_url_type(self):
        """Test that invalid URL type raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            CheckoutSessionResponse(
                checkout_url=123,  # Should be string
                session_id="cs_test_123abc"
            )


class TestWebhookEvent:
    """Test WebhookEvent schema validation."""

    def test_valid_webhook_event(self):
        """Test valid webhook event with type and data."""
        # Arrange & Act
        event = WebhookEvent(
            type="checkout.session.completed",
            data={
                "id": "cs_test_123",
                "object": "checkout.session",
                "amount_total": 5000
            }
        )

        # Assert
        assert event.type == "checkout.session.completed"
        assert event.data["id"] == "cs_test_123"
        assert event.data["amount_total"] == 5000

    def test_webhook_event_with_empty_data(self):
        """Test webhook event with empty data dict."""
        # Arrange & Act
        event = WebhookEvent(
            type="customer.created",
            data={}
        )

        # Assert
        assert event.type == "customer.created"
        assert event.data == {}

    def test_missing_type_raises_validation_error(self):
        """Test that missing type raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WebhookEvent(data={"id": "evt_123"})

        assert "type" in str(exc_info.value)

    def test_missing_data_raises_validation_error(self):
        """Test that missing data raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WebhookEvent(type="checkout.session.completed")

        assert "data" in str(exc_info.value)

    def test_invalid_data_type_raises_validation_error(self):
        """Test that non-dict data raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            WebhookEvent(
                type="checkout.session.completed",
                data="not a dict"  # Should be dict
            )


class TestEntitlementResponse:
    """Test EntitlementResponse schema validation."""

    def test_valid_entitlement_response(self):
        """Test valid entitlement response."""
        # Arrange
        now = datetime.now(UTC)

        # Act
        entitlement = EntitlementResponse(
            price_id="price_123abc",
            product_id="prod_123abc",
            product_name="AI Course Premium",
            status="active",
            created_at=now
        )

        # Assert
        assert entitlement.price_id == "price_123abc"
        assert entitlement.product_id == "prod_123abc"
        assert entitlement.product_name == "AI Course Premium"
        assert entitlement.status == "active"
        assert entitlement.created_at == now

    def test_missing_required_fields_raises_validation_error(self):
        """Test that missing required fields raise ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            EntitlementResponse(
                price_id="price_123abc",
                product_id="prod_123abc"
                # Missing product_name, status, created_at
            )

        error_str = str(exc_info.value)
        assert "product_name" in error_str
        assert "status" in error_str
        assert "created_at" in error_str

    def test_invalid_created_at_type(self):
        """Test that invalid created_at type raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            EntitlementResponse(
                price_id="price_123abc",
                product_id="prod_123abc",
                product_name="AI Course Premium",
                status="active",
                created_at="not a datetime"  # Should be datetime
            )

    def test_from_attributes_config(self):
        """Test that from_attributes config allows ORM model conversion."""
        # Arrange
        now = datetime.now(UTC)

        # Create a mock ORM object (dict simulating ORM attributes)
        class MockORMEntitlement:
            price_id = "price_123abc"
            product_id = "prod_123abc"
            product_name = "AI Course Premium"
            status = "active"
            created_at = now

        # Act
        entitlement = EntitlementResponse.model_validate(MockORMEntitlement())

        # Assert
        assert entitlement.price_id == "price_123abc"
        assert entitlement.product_id == "prod_123abc"


class TestReferralResponse:
    """Test ReferralResponse schema validation."""

    def test_valid_referral_response(self):
        """Test valid referral response."""
        # Arrange & Act
        referral = ReferralResponse(
            referral_code="REF123ABC",
            total_referrals=10,
            pending_referrals=2,
            total_credits=500
        )

        # Assert
        assert referral.referral_code == "REF123ABC"
        assert referral.total_referrals == 10
        assert referral.pending_referrals == 2
        assert referral.total_credits == 500

    def test_zero_referrals_valid(self):
        """Test that zero referrals is valid."""
        # Arrange & Act
        referral = ReferralResponse(
            referral_code="NEWUSER",
            total_referrals=0,
            pending_referrals=0,
            total_credits=0
        )

        # Assert
        assert referral.total_referrals == 0
        assert referral.pending_referrals == 0
        assert referral.total_credits == 0

    def test_missing_required_fields_raises_validation_error(self):
        """Test that missing required fields raise ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ReferralResponse(
                referral_code="REF123ABC",
                total_referrals=10
                # Missing pending_referrals, total_credits
            )

        error_str = str(exc_info.value)
        assert "pending_referrals" in error_str
        assert "total_credits" in error_str

    def test_string_referral_counts_coerced_to_int(self):
        """Test that string counts are coerced to int by Pydantic."""
        # Note: Pydantic v2 coerces string numbers to int
        # Arrange & Act
        referral = ReferralResponse(
            referral_code="REF123ABC",
            total_referrals="10",  # String coerced to int
            pending_referrals=2,
            total_credits=500
        )

        # Assert - Pydantic coerced string to int
        assert referral.total_referrals == 10
        assert isinstance(referral.total_referrals, int)

    def test_negative_referral_counts(self):
        """Test behavior with negative counts (Pydantic allows by default)."""
        # Note: If business logic requires non-negative, add validator to schema
        # Arrange & Act
        referral = ReferralResponse(
            referral_code="REF123ABC",
            total_referrals=-5,
            pending_referrals=-1,
            total_credits=-100
        )

        # Assert - Pydantic allows this without explicit constraints
        assert referral.total_referrals == -5
        assert referral.pending_referrals == -1
        assert referral.total_credits == -100


class TestStripeProductResponse:
    """Test StripeProductResponse schema validation."""

    def test_valid_product_with_all_fields(self):
        """Test valid product response with all fields."""
        # Arrange & Act
        product = StripeProductResponse(
            id="prod_123abc",
            name="AI Course Premium",
            description="Learn AI in 4 weeks",
            category="course",
            price=9900,
            price_id="price_123abc",
            currency="usd"
        )

        # Assert
        assert product.id == "prod_123abc"
        assert product.name == "AI Course Premium"
        assert product.description == "Learn AI in 4 weeks"
        assert product.category == "course"
        assert product.price == 9900
        assert product.price_id == "price_123abc"
        assert product.currency == "usd"

    def test_valid_product_with_minimal_fields(self):
        """Test valid product response with only required fields."""
        # Arrange & Act
        product = StripeProductResponse(
            id="prod_123abc",
            name="AI Course Basic",
            category="course"
        )

        # Assert
        assert product.id == "prod_123abc"
        assert product.name == "AI Course Basic"
        assert product.category == "course"
        assert product.description is None
        assert product.price is None
        assert product.price_id is None
        assert product.currency == "usd"  # Default value

    def test_missing_required_fields_raises_validation_error(self):
        """Test that missing required fields raise ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            StripeProductResponse(
                id="prod_123abc"
                # Missing name and category
            )

        error_str = str(exc_info.value)
        assert "name" in error_str
        assert "category" in error_str

    def test_string_price_coerced_to_int(self):
        """Test that string price is coerced to int by Pydantic."""
        # Note: Pydantic v2 coerces string numbers to int
        # Arrange & Act
        product = StripeProductResponse(
            id="prod_123abc",
            name="AI Course Premium",
            category="course",
            price="9900"  # String coerced to int
        )

        # Assert - Pydantic coerced string to int
        assert product.price == 9900
        assert isinstance(product.price, int)

    def test_product_with_different_currency(self):
        """Test product with non-default currency."""
        # Arrange & Act
        product = StripeProductResponse(
            id="prod_123abc",
            name="AI Course Premium EUR",
            category="course",
            price=8900,
            currency="eur"
        )

        # Assert
        assert product.currency == "eur"

    def test_from_attributes_config(self):
        """Test that from_attributes config allows ORM model conversion."""
        # Arrange
        class MockORMProduct:
            id = "prod_123abc"
            name = "AI Course Premium"
            description = "Learn AI"
            category = "course"
            price = 9900
            price_id = "price_123abc"
            currency = "usd"

        # Act
        product = StripeProductResponse.model_validate(MockORMProduct())

        # Assert
        assert product.id == "prod_123abc"
        assert product.name == "AI Course Premium"

    def test_empty_string_product_id_accepted(self):
        """Test that empty product ID is accepted by schema (no min_length constraint)."""
        # Note: Schema doesn't enforce min_length, validation happens in business logic
        # Arrange & Act
        product = StripeProductResponse(
            id="",  # Empty string allowed by schema
            name="AI Course Premium",
            category="course"
        )

        # Assert
        assert product.id == ""


class TestSchemaEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_checkout_request_with_invalid_referral_code_format(self):
        """Test checkout request with malformed referral code (allowed by schema)."""
        # Note: Schema doesn't validate format, only type
        # Arrange & Act
        request = CheckoutSessionRequest(
            product_id="prod_123abc",
            referrer_code=""  # Empty string allowed
        )

        # Assert
        assert request.referrer_code == ""

    def test_checkout_request_with_invalid_price_id_format(self):
        """Test checkout request with malformed product_id (allowed by schema)."""
        # Note: Schema validates presence, not Stripe format
        # Arrange & Act
        request = CheckoutSessionRequest(
            product_id="invalid_product_id"  # Doesn't start with 'prod_'
        )

        # Assert
        assert request.product_id == "invalid_product_id"

    def test_webhook_event_with_nested_data(self):
        """Test webhook event with complex nested data structure."""
        # Arrange & Act
        event = WebhookEvent(
            type="checkout.session.completed",
            data={
                "id": "cs_test_123",
                "customer_details": {
                    "email": "test@example.com",
                    "name": "Test User"
                },
                "line_items": [
                    {"price": "price_123", "quantity": 1},
                    {"price": "price_456", "quantity": 2}
                ],
                "metadata": {
                    "referrer_code": "REF123",
                    "user_id": "user_789"
                }
            }
        )

        # Assert
        assert event.data["customer_details"]["email"] == "test@example.com"
        assert len(event.data["line_items"]) == 2
        assert event.data["metadata"]["referrer_code"] == "REF123"

    def test_product_with_zero_price(self):
        """Test product with zero price (free product)."""
        # Arrange & Act
        product = StripeProductResponse(
            id="prod_free",
            name="Free AI Course",
            category="course",
            price=0
        )

        # Assert
        assert product.price == 0

    def test_entitlement_with_different_statuses(self):
        """Test entitlement with various status values."""
        # Note: Schema doesn't constrain status values
        # Arrange
        now = datetime.now(UTC)
        statuses = ["active", "inactive", "pending", "cancelled"]

        for status in statuses:
            # Act
            entitlement = EntitlementResponse(
                price_id="price_123",
                product_id="prod_123",
                product_name="AI Course",
                status=status,
                created_at=now
            )

            # Assert
            assert entitlement.status == status
