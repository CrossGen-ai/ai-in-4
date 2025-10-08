"""Referral service for managing user referrals and credits."""
import secrets
import string
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models import User, Referral


def generate_referral_code(length: int = 8) -> str:
    """
    Generate a unique referral code.

    Args:
        length: Length of the code (default 8)

    Returns:
        Random alphanumeric code
    """
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def ensure_user_has_referral_code(user_id: int, db: AsyncSession) -> str:
    """
    Ensure user has a referral code, create if missing.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        User's referral code
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    if user.referral_code:
        return user.referral_code

    # Generate unique code
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_referral_code()
        # Check if code already exists
        check_result = await db.execute(
            select(User).where(User.referral_code == code)
        )
        if not check_result.scalar_one_or_none():
            user.referral_code = code
            await db.commit()
            return code

    raise RuntimeError("Failed to generate unique referral code")


async def validate_referral_code(code: str, db: AsyncSession) -> Optional[User]:
    """
    Validate referral code and return referrer.

    Args:
        code: Referral code
        db: Database session

    Returns:
        User object if valid, None otherwise
    """
    result = await db.execute(
        select(User).where(User.referral_code == code, User.is_active)
    )
    return result.scalar_one_or_none()


async def create_referral(
    referrer_id: int,
    referee_email: str,
    payment_intent_id: str,
    course_id: Optional[str],
    db: AsyncSession,
) -> Referral:
    """
    Create a pending referral record.

    Args:
        referrer_id: ID of user who referred
        referee_email: Email of referred user
        payment_intent_id: Stripe payment intent ID
        course_id: Optional course ID
        db: Database session

    Returns:
        Created referral
    """
    # Prevent self-referral
    result = await db.execute(select(User).where(User.id == referrer_id))
    referrer = result.scalar_one_or_none()

    if referrer and referrer.email == referee_email:
        raise ValueError("Users cannot refer themselves")

    # Check for duplicate
    check_result = await db.execute(
        select(Referral).where(
            Referral.stripe_payment_intent_id == payment_intent_id
        )
    )
    existing = check_result.scalar_one_or_none()
    if existing:
        return existing

    referral = Referral(
        referrer_id=referrer_id,
        referee_email=referee_email,
        course_id=course_id,
        stripe_payment_intent_id=payment_intent_id,
        status="pending",
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral


async def confirm_referral(referral_id: int, db: AsyncSession) -> None:
    """
    Mark referral as confirmed.

    Args:
        referral_id: Referral ID
        db: Database session
    """
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()

    if referral:
        referral.status = "confirmed"
        await db.commit()


async def apply_referral_credit(
    referrer_id: int, amount: int, referral_id: int, db: AsyncSession
) -> None:
    """
    Apply referral credit to referrer and mark referral as credited.

    Idempotent: If referral is already credited, no action is taken.

    Args:
        referrer_id: User ID to credit
        amount: Credit amount in cents
        referral_id: Referral ID
        db: AsyncSession

    """
    # Check if referral is already credited (idempotency)
    ref_result = await db.execute(
        select(Referral).where(Referral.id == referral_id)
    )
    referral = ref_result.scalar_one_or_none()

    if not referral:
        return

    # If already credited, don't apply credit again
    if referral.status == "credited":
        return

    # Apply credit to referrer
    result = await db.execute(select(User).where(User.id == referrer_id))
    user = result.scalar_one_or_none()

    if user:
        user.referral_credits = (user.referral_credits or 0) + amount

    # Mark referral as credited
    referral.status = "credited"

    await db.commit()


async def get_referral_stats(user_id: int, db: AsyncSession) -> Dict:
    """
    Get referral statistics for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Dictionary with referral stats
    """
    # Get user for referral code and credits
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Ensure user has referral code
    referral_code = await ensure_user_has_referral_code(user_id, db)

    # Count total referrals
    total_result = await db.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    )
    total_referrals = total_result.scalar() or 0

    # Count pending referrals
    pending_result = await db.execute(
        select(func.count(Referral.id)).where(
            Referral.referrer_id == user_id, Referral.status == "pending"
        )
    )
    pending_referrals = pending_result.scalar() or 0

    return {
        "referral_code": referral_code,
        "total_referrals": total_referrals,
        "pending_referrals": pending_referrals,
        "total_credits": user.referral_credits or 0,
    }
