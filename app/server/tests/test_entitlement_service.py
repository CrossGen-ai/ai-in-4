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
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_multi_price1",
        db=test_db,
    )
    await grant_entitlement(
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


# check_course_access() Tests

@pytest.fixture
async def free_course(test_db: AsyncSession):
    """Create a free course."""
    from db.models import Course
    course = Course(
        title="Free Course",
        description="A free course",
        category="free",
        stripe_product_id=None,
    )
    test_db.add(course)
    await test_db.commit()
    await test_db.refresh(course)
    return course


@pytest.fixture
async def alacarte_course(test_db: AsyncSession, test_stripe_product: StripeProduct):
    """Create an alacarte course linked to a product."""
    from db.models import Course
    course = Course(
        title="Alacarte Course",
        description="An alacarte course",
        category="alacarte",
        stripe_product_id=test_stripe_product.id,
    )
    test_db.add(course)
    await test_db.commit()
    await test_db.refresh(course)
    return course


@pytest.fixture
async def second_alacarte_product(test_db: AsyncSession):
    """Create a second alacarte product."""
    product = StripeProduct(
        id="prod_alacarte2",
        name="Second Alacarte Product",
        description="Another alacarte product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)
    return product


@pytest.fixture
async def second_alacarte_course(test_db: AsyncSession, second_alacarte_product: StripeProduct):
    """Create a second alacarte course."""
    from db.models import Course
    course = Course(
        title="Second Alacarte Course",
        description="Another alacarte course",
        category="alacarte",
        stripe_product_id=second_alacarte_product.id,
    )
    test_db.add(course)
    await test_db.commit()
    await test_db.refresh(course)
    return course


@pytest.fixture
async def curriculum_product(test_db: AsyncSession):
    """Create a curriculum product."""
    product = StripeProduct(
        id="prod_curriculum",
        name="Full Curriculum",
        description="Complete curriculum bundle",
        category="curriculum",
        active=True,
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)
    return product


@pytest.fixture
async def curriculum_price(test_db: AsyncSession, curriculum_product: StripeProduct):
    """Create a curriculum price."""
    price = StripePrice(
        id="price_curriculum",
        product_id=curriculum_product.id,
        amount=49700,  # $497.00 in cents
        currency="usd",
        active=True,
    )
    test_db.add(price)
    await test_db.commit()
    await test_db.refresh(price)
    return price


@pytest.fixture
async def curriculum_course(test_db: AsyncSession, curriculum_product: StripeProduct):
    """Create a curriculum course."""
    from db.models import Course
    course = Course(
        title="Curriculum Course",
        description="A curriculum course",
        category="curriculum",
        stripe_product_id=curriculum_product.id,
    )
    test_db.add(course)
    await test_db.commit()
    await test_db.refresh(course)
    return course


@pytest.mark.asyncio
async def test_check_course_access_free_course_always_accessible(
    test_db: AsyncSession,
    test_user: User,
    free_course
):
    """Test free courses are always accessible without entitlement."""
    from services.entitlement_service import check_course_access

    # Act
    has_access = await check_course_access(test_user.id, free_course, test_db)

    # Assert
    assert has_access is True


@pytest.mark.asyncio
async def test_check_course_access_alacarte_with_entitlement(
    test_db: AsyncSession,
    test_user: User,
    alacarte_course,
    test_stripe_price: StripePrice
):
    """Test alacarte course is accessible with entitlement."""
    from services.entitlement_service import check_course_access

    # Arrange - grant entitlement for this specific product
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_alacarte_access",
        db=test_db,
    )

    # Act
    has_access = await check_course_access(test_user.id, alacarte_course, test_db)

    # Assert
    assert has_access is True


@pytest.mark.asyncio
async def test_check_course_access_alacarte_without_entitlement(
    test_db: AsyncSession,
    test_user: User,
    alacarte_course
):
    """Test alacarte course is not accessible without entitlement."""
    from services.entitlement_service import check_course_access

    # Act
    has_access = await check_course_access(test_user.id, alacarte_course, test_db)

    # Assert
    assert has_access is False


@pytest.mark.asyncio
async def test_check_course_access_alacarte_per_course_not_category(
    test_db: AsyncSession,
    test_user: User,
    alacarte_course,
    second_alacarte_course,
    test_stripe_price: StripePrice,
    second_alacarte_product: StripeProduct
):
    """Test buying one alacarte course does not grant access to other alacarte courses."""
    from services.entitlement_service import check_course_access

    # Arrange - grant entitlement for first course only
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_alacarte1",
        db=test_db,
    )

    # Act - check access to both courses
    has_access_first = await check_course_access(test_user.id, alacarte_course, test_db)
    has_access_second = await check_course_access(test_user.id, second_alacarte_course, test_db)

    # Assert - only first course should be accessible
    assert has_access_first is True
    assert has_access_second is False


@pytest.mark.asyncio
async def test_check_course_access_curriculum_bundle_access(
    test_db: AsyncSession,
    test_user: User,
    curriculum_course,
    curriculum_product: StripeProduct
):
    """Test curriculum courses use bundle access (any curriculum product unlocks all)."""
    from services.entitlement_service import check_course_access

    # Arrange - create curriculum price and grant entitlement
    price = StripePrice(
        id="price_curriculum",
        product_id=curriculum_product.id,
        amount=49700,
        currency="usd",
        active=True,
    )
    test_db.add(price)
    await test_db.commit()

    await grant_entitlement(
        user_id=test_user.id,
        price_id=price.id,
        payment_intent_id="pi_curriculum",
        db=test_db,
    )

    # Act
    has_access = await check_course_access(test_user.id, curriculum_course, test_db)

    # Assert
    assert has_access is True


@pytest.mark.asyncio
async def test_check_course_access_curriculum_without_entitlement(
    test_db: AsyncSession,
    test_user: User,
    curriculum_course
):
    """Test curriculum course is not accessible without any curriculum entitlement."""
    from services.entitlement_service import check_course_access

    # Act
    has_access = await check_course_access(test_user.id, curriculum_course, test_db)

    # Assert
    assert has_access is False


@pytest.mark.asyncio
async def test_check_course_access_alacarte_missing_product_id(
    test_db: AsyncSession,
    test_user: User
):
    """Test alacarte course without product_id returns False."""
    from services.entitlement_service import check_course_access
    from db.models import Course

    # Arrange - create misconfigured alacarte course
    course = Course(
        title="Broken Course",
        description="Course without product link",
        category="alacarte",
        stripe_product_id=None,  # Missing!
    )
    test_db.add(course)
    await test_db.commit()

    # Act
    has_access = await check_course_access(test_user.id, course, test_db)

    # Assert
    assert has_access is False


@pytest.mark.asyncio
async def test_check_course_access_denies_refunded_entitlement(
    test_db: AsyncSession,
    test_user: User,
    alacarte_course,
    test_stripe_price: StripePrice,
):
    """
    Test that refunded entitlements do NOT grant course access.

    Critical for ensuring users lose access after refunds.
    """
    from services.entitlement_service import check_course_access

    # Arrange - grant entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_refund_test_123",
        db=test_db,
    )

    # Act - revoke entitlement (simulates refund)
    await revoke_entitlement(entitlement.id, test_db)

    # Verify entitlement status changed to "refunded"
    await test_db.refresh(entitlement)
    assert entitlement.status == "refunded"

    # Assert - access should be denied
    has_access = await check_course_access(test_user.id, alacarte_course, test_db)
    assert has_access is False, (
        "User should NOT have access after entitlement is refunded, "
        f"but check_course_access returned {has_access}"
    )


@pytest.mark.asyncio
async def test_check_course_access_curriculum_denies_refunded_entitlement(
    test_db: AsyncSession,
    test_user: User,
    curriculum_course,
    curriculum_price: StripePrice,
):
    """
    Test that refunded curriculum entitlements do NOT grant bundle access.

    Verifies category-based access control also respects refund status.
    """
    from services.entitlement_service import check_course_access

    # Arrange - grant curriculum entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=curriculum_price.id,
        payment_intent_id="pi_curriculum_refund_test",
        db=test_db,
    )

    # Verify access granted initially
    has_access_before = await check_course_access(test_user.id, curriculum_course, test_db)
    assert has_access_before is True

    # Act - revoke entitlement
    await revoke_entitlement(entitlement.id, test_db)

    # Assert - access should be denied after refund
    has_access_after = await check_course_access(test_user.id, curriculum_course, test_db)
    assert has_access_after is False, (
        "User should NOT have curriculum access after refund"
    )
