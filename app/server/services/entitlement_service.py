"""Entitlement service for managing user course access."""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Entitlement, User, StripePrice, StripeProduct


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
