"""Entitlement service for managing user course access."""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Entitlement, StripePrice, StripeProduct, Course


async def grant_entitlement(
    user_id: int,
    price_id: str,
    payment_intent_id: str,
    db: AsyncSession,
) -> Entitlement:
    """
    Grant entitlement to a user for a specific price.

    Args:
        user_id: User ID
        price_id: Stripe price ID
        payment_intent_id: Stripe payment intent ID
        db: Database session

    Returns:
        Created entitlement
    """
    # Check if entitlement already exists (idempotency)
    result = await db.execute(
        select(Entitlement).where(
            Entitlement.stripe_payment_intent_id == payment_intent_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Create new entitlement
    entitlement = Entitlement(
        user_id=user_id,
        stripe_price_id=price_id,
        stripe_payment_intent_id=payment_intent_id,
        status="active",
    )
    db.add(entitlement)
    await db.commit()
    await db.refresh(entitlement)
    return entitlement


async def check_entitlement(
    user_id: int, price_id: str, db: AsyncSession
) -> bool:
    """
    Check if user has active entitlement for a price.

    Args:
        user_id: User ID
        price_id: Stripe price ID
        db: Database session

    Returns:
        True if user has active entitlement
    """
    result = await db.execute(
        select(Entitlement).where(
            Entitlement.user_id == user_id,
            Entitlement.stripe_price_id == price_id,
            Entitlement.status == "active",
        )
    )
    entitlement = result.scalar_one_or_none()
    return entitlement is not None


async def get_user_entitlements(
    user_id: int, db: AsyncSession
) -> List[Entitlement]:
    """
    Get all entitlements for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of entitlements
    """
    result = await db.execute(
        select(Entitlement)
        .where(Entitlement.user_id == user_id)
        .order_by(Entitlement.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_entitlement(entitlement_id: int, db: AsyncSession) -> None:
    """
    Revoke an entitlement (mark as refunded).

    Args:
        entitlement_id: Entitlement ID
        db: Database session
    """
    result = await db.execute(
        select(Entitlement).where(Entitlement.id == entitlement_id)
    )
    entitlement = result.scalar_one_or_none()
    if entitlement:
        entitlement.status = "refunded"
        await db.commit()


async def check_product_access(
    user_id: int, product_id: str, db: AsyncSession
) -> bool:
    """
    Check if user has access to a product (via any of its prices).

    Args:
        user_id: User ID
        product_id: Stripe product ID
        db: Database session

    Returns:
        True if user has access
    """
    # Get all prices for this product
    result = await db.execute(
        select(StripePrice.id).where(StripePrice.product_id == product_id)
    )
    price_ids = [row[0] for row in result.all()]

    if not price_ids:
        return False

    # Check if user has entitlement for any of these prices
    result = await db.execute(
        select(Entitlement).where(
            Entitlement.user_id == user_id,
            Entitlement.stripe_price_id.in_(price_ids),
            Entitlement.status == "active",
        )
    )
    entitlement = result.scalar_one_or_none()
    return entitlement is not None


async def check_course_access(
    user_id: int, course: Course, db: AsyncSession
) -> bool:
    """
    Check if user has access to a course based on category-based logic.

    Args:
        user_id: User ID
        course: Course object
        db: Database session

    Returns:
        True if user has access

    Access Logic:
        - free: Always accessible, no payment required
        - unique: Must have entitlement to specific stripe_product_id
        - alacarte: Must have entitlement to specific stripe_product_id (per-course access)
        - curriculum: Must have entitlement to ANY curriculum product (bundle access)
    """
    # 1. Free courses = instant access, no payment
    if course.category == "free":
        return True

    # 2. Unique/alacarte courses = check specific product entitlement
    if course.category in ["unique", "alacarte"]:
        if not course.stripe_product_id:
            # Misconfigured course with no product link
            return False
        return await check_product_access(user_id, course.stripe_product_id, db)

    # 3. Curriculum = category-based access (any curriculum product unlocks all)
    if course.category == "curriculum":
        result = await db.execute(
            select(Entitlement)
            .join(StripePrice, Entitlement.stripe_price_id == StripePrice.id)
            .join(StripeProduct, StripePrice.product_id == StripeProduct.id)
            .where(
                Entitlement.user_id == user_id,
                Entitlement.status == "active",
                StripeProduct.category == "curriculum",
            )
        )
        entitlement = result.scalar_one_or_none()
        return entitlement is not None

    # Unknown category - deny access
    return False
