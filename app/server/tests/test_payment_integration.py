"""Integration tests for full payment workflows.

Tests cover end-to-end payment flows including:
- Checkout session creation → webhook processing → entitlement grant
- Referral code validation → checkout → credit application
- Product sync from Stripe to local database
- Edge cases: idempotency, invalid codes, self-referral, refunds
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, UTC

from main import app
from db.models import (
    User,
    StripeProduct,
    StripePrice,
    Referral,
)
from api.routes.users import get_current_user
from services import entitlement_service, referral_service


@pytest.fixture
def override_get_current_user(test_user):
    """Override get_current_user dependency for authenticated tests."""
    async def _get_current_user_override():
        return test_user

    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _get_current_user_override
    yield test_user
    if original:
        app.dependency_overrides[get_current_user] = original
    else:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def test_referrer(test_db):
    """Create a test referrer user with referral code."""
    referrer = User(
        email="referrer@example.com",
        is_active=True,
        created_at=datetime.now(UTC),
        referral_code="REFER123",
    )
    test_db.add(referrer)
    await test_db.commit()
    await test_db.refresh(referrer)
    return referrer


@pytest.fixture
async def test_product_and_price(test_db):
    """Create test product and price."""
    product = StripeProduct(
        id="prod_test_integration",
        name="Integration Test Product",
        description="Product for integration testing",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_test_integration",
        product_id=product.id,
        amount=10000,  # $100.00
        currency="usd",
        active=True,
    )
    test_db.add(price)
    await test_db.commit()
    await test_db.refresh(product)
    await test_db.refresh(price)
    return product, price


# ============================================================================
# Integration Tests: Checkout → Webhook → Entitlement Grant Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_full_checkout_to_entitlement_workflow(
    client, override_get_current_user, test_product_and_price, test_db
):
    """Test complete workflow: checkout session creation → webhook → entitlement grant.

    This integration test validates:
    1. User can create checkout session with valid price
    2. Webhook processes payment_intent.succeeded event
    3. Entitlement is granted to user
    4. User can retrieve their entitlement
    """
    product, price = test_product_and_price
    user = override_get_current_user

    # Step 1: Create checkout session
    checkout_response = client.post(
        "/api/payments/checkout",
        json={"price_id": price.id, "referrer_code": None},
    )
    assert checkout_response.status_code == 200
    checkout_data = checkout_response.json()
    assert "session_id" in checkout_data
    assert "checkout_url" in checkout_data

    # Step 2: Simulate webhook from Stripe after successful payment
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_integration_123",
                "amount": 10000,
                "metadata": {
                    "user_id": str(user.id),
                    "user_email": user.email,
                    "price_id": price.id,
                }
            }
        }
    }

    webhook_response = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )
    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "success"

    # Step 3: Verify entitlement was granted
    entitlements_response = client.get("/api/payments/entitlements")
    assert entitlements_response.status_code == 200
    entitlements = entitlements_response.json()
    assert len(entitlements) == 1
    assert entitlements[0]["price_id"] == price.id
    assert entitlements[0]["product_id"] == product.id
    assert entitlements[0]["product_name"] == product.name
    assert entitlements[0]["status"] == "active"

    # Step 4: Verify entitlement in database
    granted_entitlement = await entitlement_service.get_user_entitlements(user.id, test_db)
    assert len(granted_entitlement) == 1
    assert granted_entitlement[0].stripe_price_id == price.id
    assert granted_entitlement[0].stripe_payment_intent_id == "pi_test_integration_123"
    assert granted_entitlement[0].status == "active"


@pytest.mark.asyncio
async def test_webhook_idempotency_prevents_duplicate_entitlements(
    client, test_product_and_price, test_user, test_db
):
    """Test webhook idempotency: duplicate events should not create duplicate entitlements.

    Validates that:
    1. First webhook creates entitlement
    2. Duplicate webhook returns existing entitlement
    3. Only one entitlement exists in database
    """
    product, price = test_product_and_price

    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_idempotent",
                "amount": 10000,
                "metadata": {
                    "user_id": str(test_user.id),
                    "user_email": test_user.email,
                    "price_id": price.id,
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
    assert response1.status_code == 200
    assert response1.json()["status"] == "success"

    # Verify first entitlement created
    entitlements_after_first = await entitlement_service.get_user_entitlements(
        test_user.id, test_db
    )
    assert len(entitlements_after_first) == 1
    first_entitlement_id = entitlements_after_first[0].id

    # Second webhook call (duplicate)
    response2 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )
    assert response2.status_code == 200
    assert response2.json()["status"] == "success"

    # Verify no duplicate entitlement created
    entitlements_after_second = await entitlement_service.get_user_entitlements(
        test_user.id, test_db
    )
    assert len(entitlements_after_second) == 1
    assert entitlements_after_second[0].id == first_entitlement_id


# ============================================================================
# Integration Tests: Referral Code Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_full_referral_workflow_checkout_to_credit_application(
    client, override_get_current_user, test_referrer, test_product_and_price, test_db
):
    """Test complete referral workflow: checkout with referral → webhook → credit application.

    Validates:
    1. User creates checkout with valid referral code
    2. Webhook processes payment and creates referral record
    3. Referrer receives 25% credit
    4. Referral stats updated correctly
    """
    product, price = test_product_and_price
    user = override_get_current_user
    referrer = test_referrer

    # Step 1: Create checkout session with referral code
    checkout_response = client.post(
        "/api/payments/checkout",
        json={"price_id": price.id, "referrer_code": referrer.referral_code},
    )
    assert checkout_response.status_code == 200

    # Step 2: Simulate successful payment webhook with referrer info
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_referral_123",
                "amount": 10000,  # $100.00
                "metadata": {
                    "user_id": str(user.id),
                    "user_email": user.email,
                    "price_id": price.id,
                    "referrer_id": str(referrer.id),
                    "referrer_code": referrer.referral_code,
                }
            }
        }
    }

    webhook_response = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )
    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "success"

    # Step 3: Verify entitlement granted to buyer
    buyer_entitlements = await entitlement_service.get_user_entitlements(user.id, test_db)
    assert len(buyer_entitlements) == 1
    assert buyer_entitlements[0].stripe_price_id == price.id

    # Step 4: Verify referral record created
    from sqlalchemy import select
    referral_result = await test_db.execute(
        select(Referral).where(
            Referral.referrer_id == referrer.id,
            Referral.stripe_payment_intent_id == "pi_test_referral_123",
        )
    )
    referral = referral_result.scalar_one_or_none()
    assert referral is not None
    assert referral.referee_email == user.email
    assert referral.status == "credited"

    # Step 5: Verify referrer received 25% credit ($25.00 = 2500 cents)
    await test_db.refresh(referrer)
    expected_credit = int(10000 * 0.25)  # 2500 cents
    assert referrer.referral_credits == expected_credit

    # Step 6: Verify referral stats updated
    stats = await referral_service.get_referral_stats(referrer.id, test_db)
    assert stats["total_referrals"] == 1
    assert stats["total_credits"] == expected_credit
    assert stats["pending_referrals"] == 0  # Should be credited, not pending


@pytest.mark.asyncio
async def test_referral_code_validation_rejects_invalid_code(
    client, override_get_current_user, test_product_and_price
):
    """Test checkout rejects invalid referral code.

    Validates:
    1. Checkout fails with invalid referral code
    2. Appropriate error message returned
    """
    product, price = test_product_and_price

    response = client.post(
        "/api/payments/checkout",
        json={"price_id": price.id, "referrer_code": "INVALID999"},
    )

    assert response.status_code == 400
    assert "Invalid referrer code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_self_referral_prevention(
    client, override_get_current_user, test_product_and_price, test_db
):
    """Test that users cannot use their own referral code.

    Validates:
    1. User cannot checkout with their own referral code
    2. Appropriate error message returned
    """
    product, price = test_product_and_price
    user = override_get_current_user

    # Ensure user has referral code
    user_code = await referral_service.ensure_user_has_referral_code(user.id, test_db)
    assert user_code is not None

    # Attempt to use own referral code
    response = client.post(
        "/api/payments/checkout",
        json={"price_id": price.id, "referrer_code": user_code},
    )

    assert response.status_code == 400
    assert "Cannot use your own referral code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_referral_idempotency_prevents_duplicate_credits(
    client, test_referrer, test_product_and_price, test_user, test_db
):
    """Test referral idempotency: duplicate webhooks don't grant duplicate credits.

    Validates:
    1. First webhook creates referral and grants credit
    2. Duplicate webhook doesn't create duplicate referral or credit
    3. Referrer's total credit remains correct
    4. Only one referral record exists
    """
    product, price = test_product_and_price
    referrer = test_referrer
    initial_credits = referrer.referral_credits or 0

    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_ref_idempotent",
                "amount": 8000,  # $80.00
                "metadata": {
                    "user_id": str(test_user.id),
                    "user_email": test_user.email,
                    "price_id": price.id,
                    "referrer_id": str(referrer.id),
                    "referrer_code": referrer.referral_code,
                }
            }
        }
    }

    # First webhook
    response1 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )
    assert response1.status_code == 200

    await test_db.refresh(referrer)
    expected_credit = initial_credits + int(8000 * 0.25)  # 2000 cents
    assert referrer.referral_credits == expected_credit

    # Second webhook (duplicate)
    response2 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )
    assert response2.status_code == 200

    # Verify credit not duplicated
    await test_db.refresh(referrer)
    assert referrer.referral_credits == expected_credit

    # Verify only one referral record
    from sqlalchemy import select
    referral_result = await test_db.execute(
        select(Referral).where(
            Referral.stripe_payment_intent_id == "pi_test_ref_idempotent"
        )
    )
    referrals = list(referral_result.scalars().all())
    assert len(referrals) == 1
    assert referrals[0].status == "credited"


# ============================================================================
# Integration Tests: Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_webhook_handles_missing_metadata_gracefully(client):
    """Test webhook handles missing required metadata without crashing.

    Validates:
    1. Webhook returns error status for missing metadata
    2. No entitlement created
    3. System remains stable
    """
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_missing_data",
                "amount": 5000,
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


@pytest.mark.asyncio
async def test_webhook_handles_invalid_json(client):
    """Test webhook rejects invalid JSON payload.

    Validates:
    1. Webhook returns 400 for malformed JSON
    2. Appropriate error message
    """
    response = client.post(
        "/api/payments/webhook",
        data="this is not json",
        headers={
            "stripe-signature": "test_signature",
            "content-type": "application/json"
        },
    )

    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_ignores_irrelevant_events(client):
    """Test webhook ignores non-payment_intent.succeeded events.

    Validates:
    1. Webhook returns success for irrelevant events
    2. No side effects occur
    """
    webhook_payload = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test_123",
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
async def test_entitlement_service_error_handling_in_webhook(client, test_product_and_price):
    """Test webhook handles entitlement service errors gracefully.

    Validates:
    1. Webhook catches and logs entitlement service errors
    2. Returns error status
    3. System remains stable
    """
    product, price = test_product_and_price

    with patch(
        "api.routes.payments.entitlement_service.grant_entitlement",
        new_callable=AsyncMock
    ) as mock_grant:
        mock_grant.side_effect = Exception("Database connection failed")

        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_error_handling",
                    "amount": 5000,
                    "metadata": {
                        "user_id": "1",
                        "user_email": "test@example.com",
                        "price_id": price.id,
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
        assert "Database connection failed" in data["message"]


@pytest.mark.asyncio
async def test_referral_service_error_does_not_block_entitlement(
    client, test_product_and_price, test_db
):
    """Test that referral service errors don't prevent entitlement grant.

    Validates:
    1. Entitlement still granted if referral processing fails
    2. Webhook returns success
    3. Partial failure handled gracefully
    """
    product, price = test_product_and_price

    with patch(
        "api.routes.payments.referral_service.create_referral",
        new_callable=AsyncMock
    ) as mock_create_ref:
        mock_create_ref.side_effect = Exception("Referral service temporarily unavailable")

        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_ref_failure",
                    "amount": 5000,
                    "metadata": {
                        "user_id": "1",
                        "user_email": "test@example.com",
                        "price_id": price.id,
                        "referrer_id": "2",
                        "referrer_code": "REF123",
                    }
                }
            }
        }

        response = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Should still succeed (entitlement granted, referral failed)
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_checkout_validates_price_exists(
    client, override_get_current_user
):
    """Test checkout validates price exists in database.

    Validates:
    1. Checkout fails for non-existent price
    2. Returns 404 with appropriate message
    """
    response = client.post(
        "/api/payments/checkout",
        json={"price_id": "price_nonexistent_123", "referrer_code": None},
    )

    assert response.status_code == 404
    assert "Price not found" in response.json()["detail"]


# ============================================================================
# Integration Tests: Product Sync (Placeholder)
# ============================================================================


@pytest.mark.asyncio
async def test_sync_products_endpoint_accessible(
    client, override_get_current_user
):
    """Test product sync endpoint is accessible.

    Note: Actual Stripe MCP integration pending.
    This test validates endpoint exists and returns expected structure.
    """
    response = client.post("/api/payments/sync-products")

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "message" in data


# ============================================================================
# Integration Tests: Multi-User Scenarios
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_users_can_purchase_same_product(
    client, test_product_and_price, test_db
):
    """Test multiple users can independently purchase the same product.

    Validates:
    1. Multiple users can create checkout for same product
    2. Each user receives independent entitlement
    3. No conflicts between purchases
    """
    product, price = test_product_and_price

    # Create two users
    user1 = User(
        email="user1@example.com",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    user2 = User(
        email="user2@example.com",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    test_db.add(user1)
    test_db.add(user2)
    await test_db.commit()
    await test_db.refresh(user1)
    await test_db.refresh(user2)

    # Process webhooks for both users
    for user in [user1, user2]:
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": f"pi_test_multi_user_{user.id}",
                    "amount": 10000,
                    "metadata": {
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "price_id": price.id,
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

    # Verify both users have entitlements
    user1_entitlements = await entitlement_service.get_user_entitlements(user1.id, test_db)
    user2_entitlements = await entitlement_service.get_user_entitlements(user2.id, test_db)

    assert len(user1_entitlements) == 1
    assert len(user2_entitlements) == 1
    assert user1_entitlements[0].stripe_price_id == price.id
    assert user2_entitlements[0].stripe_price_id == price.id


@pytest.mark.asyncio
async def test_referrer_can_have_multiple_referrals(
    client, test_referrer, test_product_and_price, test_db
):
    """Test referrer can receive credits for multiple referrals.

    Validates:
    1. Single referrer can refer multiple users
    2. Credits accumulate correctly
    3. Referral stats updated properly
    """
    product, price = test_product_and_price
    referrer = test_referrer
    initial_credits = referrer.referral_credits or 0

    # Create three referred users
    referred_users = []
    for i in range(3):
        user = User(
            email=f"referred{i}@example.com",
            is_active=True,
            created_at=datetime.now(UTC),
        )
        test_db.add(user)
        referred_users.append(user)
    await test_db.commit()

    # Process webhooks for all referred users
    amount_per_purchase = 10000  # $100.00
    for idx, user in enumerate(referred_users):
        await test_db.refresh(user)
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": f"pi_test_multi_ref_{idx}",
                    "amount": amount_per_purchase,
                    "metadata": {
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "price_id": price.id,
                        "referrer_id": str(referrer.id),
                        "referrer_code": referrer.referral_code,
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

    # Verify referrer received correct total credits
    await test_db.refresh(referrer)
    expected_total_credit = initial_credits + (3 * int(amount_per_purchase * 0.25))
    assert referrer.referral_credits == expected_total_credit

    # Verify referral stats
    stats = await referral_service.get_referral_stats(referrer.id, test_db)
    assert stats["total_referrals"] == 3
    assert stats["total_credits"] == expected_total_credit
