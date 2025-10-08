"""Tests for user entitlement management with async database fixtures."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.entitlement_service import (
    grant_entitlement,
    check_entitlement,
    get_user_entitlements,
    revoke_entitlement,
    check_product_access,
)
from db.models import Entitlement, StripePrice, StripeProduct, User


# Fixtures

@pytest.fixture
async def test_stripe_product(test_db: AsyncSession):
    """Create a test Stripe product."""
    product = StripeProduct(
        id="prod_test123",
        name="Test Course",
        description="A test course product",
        category="curriculum",
        active=True,
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)
    return product


@pytest.fixture
async def test_stripe_price(test_db: AsyncSession, test_stripe_product: StripeProduct):
    """Create a test Stripe price."""
    price = StripePrice(
        id="price_test123",
        product_id=test_stripe_product.id,
        amount=9900,  # $99.00 in cents
        currency="usd",
        active=True,
    )
    test_db.add(price)
    await test_db.commit()
    await test_db.refresh(price)
    return price


@pytest.fixture
async def second_test_stripe_price(test_db: AsyncSession, test_stripe_product: StripeProduct):
    """Create a second test Stripe price for the same product."""
    price = StripePrice(
        id="price_test456",
        product_id=test_stripe_product.id,
        amount=14900,  # $149.00 in cents
        currency="usd",
        active=True,
    )
    test_db.add(price)
    await test_db.commit()
    await test_db.refresh(price)
    return price


# Happy Path Tests

@pytest.mark.asyncio
async def test_grant_entitlement_creates_record(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test grant_entitlement creates entitlement record."""
    # Arrange
    payment_intent_id = "pi_test123"

    # Act
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id=payment_intent_id,
        db=test_db,
    )

    # Assert
    assert entitlement.id is not None
    assert entitlement.user_id == test_user.id
    assert entitlement.stripe_price_id == test_stripe_price.id
    assert entitlement.stripe_payment_intent_id == payment_intent_id
    assert entitlement.status == "active"


@pytest.mark.asyncio
async def test_grant_entitlement_idempotent(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test grant_entitlement is idempotent for same payment intent."""
    # Arrange
    payment_intent_id = "pi_idempotent123"

    # Act - call twice with same payment intent
    entitlement_1 = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id=payment_intent_id,
        db=test_db,
    )
    entitlement_2 = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id=payment_intent_id,
        db=test_db,
    )

    # Assert - should return same entitlement
    assert entitlement_1.id == entitlement_2.id


@pytest.mark.asyncio
async def test_check_entitlement_verifies_active_entitlement(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test check_entitlement verifies user has active entitlement."""
    # Arrange - create entitlement first
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_check123",
        db=test_db,
    )

    # Act
    has_entitlement = await check_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        db=test_db,
    )

    # Assert
    assert has_entitlement is True


@pytest.mark.asyncio
async def test_check_entitlement_returns_false_when_none(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test check_entitlement returns False when no entitlement exists."""
    # Act
    has_entitlement = await check_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        db=test_db,
    )

    # Assert
    assert has_entitlement is False


@pytest.mark.asyncio
async def test_get_user_entitlements_returns_all_entitlements(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test get_user_entitlements returns all user entitlements."""
    # Arrange - create multiple entitlements
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_multi1",
        db=test_db,
    )
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_multi2",
        db=test_db,
    )

    # Act
    entitlements = await get_user_entitlements(test_user.id, test_db)

    # Assert
    assert len(entitlements) == 2
    assert all(e.user_id == test_user.id for e in entitlements)


@pytest.mark.asyncio
async def test_get_user_entitlements_returns_empty_list(
    test_db: AsyncSession,
    test_user: User
):
    """Test get_user_entitlements returns empty list when no entitlements."""
    # Act
    entitlements = await get_user_entitlements(test_user.id, test_db)

    # Assert
    assert entitlements == []


@pytest.mark.asyncio
async def test_revoke_entitlement_marks_as_refunded(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test revoke_entitlement marks entitlement as refunded."""
    # Arrange - create entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_revoke123",
        db=test_db,
    )

    # Act
    await revoke_entitlement(entitlement.id, test_db)

    # Assert - verify status changed
    result = await test_db.execute(
        select(Entitlement).where(Entitlement.id == entitlement.id)
    )
    updated_entitlement = result.scalar_one()
    assert updated_entitlement.status == "refunded"


@pytest.mark.asyncio
async def test_check_product_access_with_active_entitlement(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice,
    test_stripe_product: StripeProduct
):
    """Test check_product_access returns True when user has access."""
    # Arrange - grant entitlement
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_product123",
        db=test_db,
    )

    # Act
    has_access = await check_product_access(
        user_id=test_user.id,
        product_id=test_stripe_product.id,
        db=test_db,
    )

    # Assert
    assert has_access is True


@pytest.mark.asyncio
async def test_check_product_access_without_entitlement(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_product: StripeProduct
):
    """Test check_product_access returns False when no entitlement."""
    # Act
    has_access = await check_product_access(
        user_id=test_user.id,
        product_id=test_stripe_product.id,
        db=test_db,
    )

    # Assert
    assert has_access is False


# Edge Cases

@pytest.mark.asyncio
async def test_check_entitlement_ignores_refunded_status(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test check_entitlement returns False for refunded entitlements."""
    # Arrange - create and revoke entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_refunded123",
        db=test_db,
    )
    await revoke_entitlement(entitlement.id, test_db)

    # Act
    has_entitlement = await check_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        db=test_db,
    )

    # Assert
    assert has_entitlement is False


@pytest.mark.asyncio
async def test_get_user_entitlements_ordered_by_created_at_desc(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice
):
    """Test get_user_entitlements returns entitlements in descending order."""
    # Arrange - create entitlements in sequence
    first = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_first",
        db=test_db,
    )
    second = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_second",
        db=test_db,
    )

    # Act
    entitlements = await get_user_entitlements(test_user.id, test_db)

    # Assert - most recent first
    assert entitlements[0].id == second.id
    assert entitlements[1].id == first.id


@pytest.mark.asyncio
async def test_multiple_entitlements_for_same_user(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice,
    second_test_stripe_price: StripePrice
):
    """Test user can have multiple entitlements for different prices."""
    # Arrange & Act - create entitlements for different prices
    entitlement_1 = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_multi_price1",
        db=test_db,
    )
    entitlement_2 = await grant_entitlement(
        user_id=test_user.id,
        price_id=second_test_stripe_price.id,
        payment_intent_id="pi_multi_price2",
        db=test_db,
    )

    # Assert - both entitlements exist and are active
    entitlements = await get_user_entitlements(test_user.id, test_db)
    assert len(entitlements) == 2
    assert all(e.status == "active" for e in entitlements)


@pytest.mark.asyncio
async def test_revoke_entitlement_with_nonexistent_id(test_db: AsyncSession):
    """Test revoke_entitlement handles nonexistent entitlement gracefully."""
    # Act - attempt to revoke non-existent entitlement
    await revoke_entitlement(entitlement_id=99999, db=test_db)

    # Assert - no exception raised, operation is a no-op


@pytest.mark.asyncio
async def test_check_product_access_with_multiple_prices(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice,
    second_test_stripe_price: StripePrice,
    test_stripe_product: StripeProduct
):
    """Test check_product_access works with any price for the product."""
    # Arrange - grant entitlement for second price only
    await grant_entitlement(
        user_id=test_user.id,
        price_id=second_test_stripe_price.id,
        payment_intent_id="pi_multi_price_access",
        db=test_db,
    )

    # Act
    has_access = await check_product_access(
        user_id=test_user.id,
        product_id=test_stripe_product.id,
        db=test_db,
    )

    # Assert - should have access via second price
    assert has_access is True


@pytest.mark.asyncio
async def test_check_product_access_with_no_prices(test_db: AsyncSession, test_user: User):
    """Test check_product_access returns False for product with no prices."""
    # Arrange - create product without prices
    product = StripeProduct(
        id="prod_no_prices",
        name="Product Without Prices",
        description="Test product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.commit()

    # Act
    has_access = await check_product_access(
        user_id=test_user.id,
        product_id=product.id,
        db=test_db,
    )

    # Assert
    assert has_access is False


@pytest.mark.asyncio
async def test_check_product_access_ignores_refunded_entitlements(
    test_db: AsyncSession,
    test_user: User,
    test_stripe_price: StripePrice,
    test_stripe_product: StripeProduct
):
    """Test check_product_access returns False for refunded entitlements."""
    # Arrange - grant and then revoke entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_product_refunded",
        db=test_db,
    )
    await revoke_entitlement(entitlement.id, test_db)

    # Act
    has_access = await check_product_access(
        user_id=test_user.id,
        product_id=test_stripe_product.id,
        db=test_db,
    )

    # Assert
    assert has_access is False
