"""Tests for referral tracking and credit management."""
import pytest
from datetime import datetime, UTC
from sqlalchemy import select

from services.referral_service import (
    generate_referral_code,
    ensure_user_has_referral_code,
    validate_referral_code,
    create_referral,
    confirm_referral,
    apply_referral_credit,
    get_referral_stats,
)
from db.models import User, Referral


# ============================================================================
# Test generate_referral_code
# ============================================================================


def test_generate_referral_code_default_length():
    """Test generate_referral_code generates 8-character code by default."""
    # Act
    code = generate_referral_code()

    # Assert
    assert len(code) == 8


def test_generate_referral_code_custom_length():
    """Test generate_referral_code respects custom length parameter."""
    # Act
    code = generate_referral_code(length=12)

    # Assert
    assert len(code) == 12


def test_generate_referral_code_uppercase_and_digits_only():
    """Test generate_referral_code uses only uppercase letters and digits."""
    # Act
    code = generate_referral_code()

    # Assert
    assert code.isupper() or code.isdigit()
    assert code.isalnum()


def test_generate_referral_code_uniqueness():
    """Test generate_referral_code generates different codes."""
    # Act
    codes = [generate_referral_code() for _ in range(100)]

    # Assert - at least 95% should be unique (allows for rare collisions)
    unique_codes = set(codes)
    assert len(unique_codes) >= 95


# ============================================================================
# Test ensure_user_has_referral_code
# ============================================================================


@pytest.mark.asyncio
async def test_ensure_user_has_referral_code_creates_new_code(test_db, test_user):
    """Test ensure_user_has_referral_code creates code for user without one."""
    # Arrange
    assert test_user.referral_code is None

    # Act
    code = await ensure_user_has_referral_code(test_user.id, test_db)

    # Assert
    assert code is not None
    assert len(code) == 8
    await test_db.refresh(test_user)
    assert test_user.referral_code == code


@pytest.mark.asyncio
async def test_ensure_user_has_referral_code_returns_existing_code(test_db, test_user):
    """Test ensure_user_has_referral_code returns existing code if present."""
    # Arrange
    existing_code = "TESTCODE"
    test_user.referral_code = existing_code
    await test_db.commit()

    # Act
    code = await ensure_user_has_referral_code(test_user.id, test_db)

    # Assert
    assert code == existing_code


@pytest.mark.asyncio
async def test_ensure_user_has_referral_code_nonexistent_user(test_db):
    """Test ensure_user_has_referral_code raises ValueError for nonexistent user."""
    # Act & Assert
    with pytest.raises(ValueError, match="User 99999 not found"):
        await ensure_user_has_referral_code(99999, test_db)


@pytest.mark.asyncio
async def test_ensure_user_has_referral_code_unique_code_generation(test_db):
    """Test ensure_user_has_referral_code generates unique codes for multiple users."""
    # Arrange
    user1 = User(email="user1@example.com", is_active=True, created_at=datetime.now(UTC))
    user2 = User(email="user2@example.com", is_active=True, created_at=datetime.now(UTC))
    test_db.add_all([user1, user2])
    await test_db.commit()
    await test_db.refresh(user1)
    await test_db.refresh(user2)

    # Act
    code1 = await ensure_user_has_referral_code(user1.id, test_db)
    code2 = await ensure_user_has_referral_code(user2.id, test_db)

    # Assert
    assert code1 != code2


# ============================================================================
# Test validate_referral_code
# ============================================================================


@pytest.mark.asyncio
async def test_validate_referral_code_valid_code(test_db, test_user):
    """Test validate_referral_code returns user for valid code."""
    # Arrange
    code = "VALID123"
    test_user.referral_code = code
    test_user.is_active = True
    await test_db.commit()

    # Act
    result = await validate_referral_code(code, test_db)

    # Assert
    assert result is not None
    assert result.id == test_user.id
    assert result.email == test_user.email


@pytest.mark.asyncio
async def test_validate_referral_code_invalid_code(test_db):
    """Test validate_referral_code returns None for invalid code."""
    # Act
    result = await validate_referral_code("INVALID1", test_db)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_validate_referral_code_inactive_user(test_db, test_user):
    """Test validate_referral_code returns None for inactive user's code."""
    # Arrange
    code = "INACTIVE"
    test_user.referral_code = code
    test_user.is_active = False
    await test_db.commit()

    # Act
    result = await validate_referral_code(code, test_db)

    # Assert
    assert result is None


# ============================================================================
# Test create_referral
# ============================================================================


@pytest.mark.asyncio
async def test_create_referral_success(test_db, test_user):
    """Test create_referral creates pending referral record."""
    # Arrange
    referee_email = "referee@example.com"
    payment_intent_id = "pi_test123"
    course_id = "course_001"

    # Act
    referral = await create_referral(
        referrer_id=test_user.id,
        referee_email=referee_email,
        payment_intent_id=payment_intent_id,
        course_id=course_id,
        db=test_db,
    )

    # Assert
    assert referral is not None
    assert referral.referrer_id == test_user.id
    assert referral.referee_email == referee_email
    assert referral.stripe_payment_intent_id == payment_intent_id
    assert referral.course_id == course_id
    assert referral.status == "pending"


@pytest.mark.asyncio
async def test_create_referral_self_referral_prevention(test_db, test_user):
    """Test create_referral prevents self-referral."""
    # Act & Assert
    with pytest.raises(ValueError, match="Users cannot refer themselves"):
        await create_referral(
            referrer_id=test_user.id,
            referee_email=test_user.email,
            payment_intent_id="pi_test123",
            course_id=None,
            db=test_db,
        )


@pytest.mark.asyncio
async def test_create_referral_duplicate_payment_intent(test_db, test_user):
    """Test create_referral returns existing referral for duplicate payment intent."""
    # Arrange
    payment_intent_id = "pi_duplicate"
    referee_email = "referee@example.com"

    # Create first referral
    first_referral = await create_referral(
        referrer_id=test_user.id,
        referee_email=referee_email,
        payment_intent_id=payment_intent_id,
        course_id=None,
        db=test_db,
    )

    # Act - try to create duplicate
    second_referral = await create_referral(
        referrer_id=test_user.id,
        referee_email=referee_email,
        payment_intent_id=payment_intent_id,
        course_id=None,
        db=test_db,
    )

    # Assert
    assert first_referral.id == second_referral.id


@pytest.mark.asyncio
async def test_create_referral_without_course_id(test_db, test_user):
    """Test create_referral works with None course_id."""
    # Act
    referral = await create_referral(
        referrer_id=test_user.id,
        referee_email="referee@example.com",
        payment_intent_id="pi_nocourse",
        course_id=None,
        db=test_db,
    )

    # Assert
    assert referral.course_id is None


# ============================================================================
# Test confirm_referral
# ============================================================================


@pytest.mark.asyncio
async def test_confirm_referral_success(test_db, test_user):
    """Test confirm_referral marks referral as confirmed."""
    # Arrange
    referral = Referral(
        referrer_id=test_user.id,
        referee_email="referee@example.com",
        stripe_payment_intent_id="pi_confirm",
        status="pending",
        created_at=datetime.now(UTC),
    )
    test_db.add(referral)
    await test_db.commit()
    await test_db.refresh(referral)

    # Act
    await confirm_referral(referral.id, test_db)

    # Assert
    await test_db.refresh(referral)
    assert referral.status == "confirmed"


@pytest.mark.asyncio
async def test_confirm_referral_nonexistent_referral(test_db):
    """Test confirm_referral handles nonexistent referral gracefully."""
    # Act - should not raise error
    await confirm_referral(99999, test_db)

    # Assert - no exception raised


# ============================================================================
# Test apply_referral_credit
# ============================================================================


@pytest.mark.asyncio
async def test_apply_referral_credit_updates_user_balance(test_db, test_user):
    """Test apply_referral_credit updates user's credit balance."""
    # Arrange
    initial_credits = test_user.referral_credits or 0
    referral = Referral(
        referrer_id=test_user.id,
        referee_email="referee@example.com",
        stripe_payment_intent_id="pi_credit",
        status="confirmed",
        created_at=datetime.now(UTC),
    )
    test_db.add(referral)
    await test_db.commit()
    await test_db.refresh(referral)

    credit_amount = 500  # $5.00

    # Act
    await apply_referral_credit(test_user.id, credit_amount, referral.id, test_db)

    # Assert
    await test_db.refresh(test_user)
    assert test_user.referral_credits == initial_credits + credit_amount


@pytest.mark.asyncio
async def test_apply_referral_credit_marks_referral_as_credited(test_db, test_user):
    """Test apply_referral_credit marks referral status as credited."""
    # Arrange
    referral = Referral(
        referrer_id=test_user.id,
        referee_email="referee@example.com",
        stripe_payment_intent_id="pi_credited",
        status="confirmed",
        created_at=datetime.now(UTC),
    )
    test_db.add(referral)
    await test_db.commit()
    await test_db.refresh(referral)

    # Act
    await apply_referral_credit(test_user.id, 500, referral.id, test_db)

    # Assert
    await test_db.refresh(referral)
    assert referral.status == "credited"


@pytest.mark.asyncio
async def test_apply_referral_credit_accumulates_credits(test_db, test_user):
    """Test apply_referral_credit accumulates multiple credits."""
    # Arrange
    test_user.referral_credits = 1000  # $10.00
    await test_db.commit()

    referral = Referral(
        referrer_id=test_user.id,
        referee_email="referee@example.com",
        stripe_payment_intent_id="pi_accumulate",
        status="confirmed",
        created_at=datetime.now(UTC),
    )
    test_db.add(referral)
    await test_db.commit()
    await test_db.refresh(referral)

    # Act
    await apply_referral_credit(test_user.id, 500, referral.id, test_db)

    # Assert
    await test_db.refresh(test_user)
    assert test_user.referral_credits == 1500


@pytest.mark.asyncio
async def test_apply_referral_credit_nonexistent_user(test_db):
    """Test apply_referral_credit handles nonexistent user gracefully."""
    # Act - should not raise error
    await apply_referral_credit(99999, 500, 1, test_db)

    # Assert - no exception raised


# ============================================================================
# Test get_referral_stats
# ============================================================================


@pytest.mark.asyncio
async def test_get_referral_stats_returns_stats(test_db, test_user):
    """Test get_referral_stats returns referral statistics."""
    # Arrange
    test_user.referral_code = "STATS123"
    test_user.referral_credits = 1500
    await test_db.commit()

    # Create some referrals
    referral1 = Referral(
        referrer_id=test_user.id,
        referee_email="ref1@example.com",
        stripe_payment_intent_id="pi_stats1",
        status="credited",
        created_at=datetime.now(UTC),
    )
    referral2 = Referral(
        referrer_id=test_user.id,
        referee_email="ref2@example.com",
        stripe_payment_intent_id="pi_stats2",
        status="pending",
        created_at=datetime.now(UTC),
    )
    referral3 = Referral(
        referrer_id=test_user.id,
        referee_email="ref3@example.com",
        stripe_payment_intent_id="pi_stats3",
        status="confirmed",
        created_at=datetime.now(UTC),
    )
    test_db.add_all([referral1, referral2, referral3])
    await test_db.commit()

    # Act
    stats = await get_referral_stats(test_user.id, test_db)

    # Assert
    assert stats["referral_code"] == "STATS123"
    assert stats["total_referrals"] == 3
    assert stats["pending_referrals"] == 1
    assert stats["total_credits"] == 1500


@pytest.mark.asyncio
async def test_get_referral_stats_creates_code_if_missing(test_db, test_user):
    """Test get_referral_stats creates referral code if user doesn't have one."""
    # Arrange
    assert test_user.referral_code is None

    # Act
    stats = await get_referral_stats(test_user.id, test_db)

    # Assert
    assert stats["referral_code"] is not None
    assert len(stats["referral_code"]) == 8
    await test_db.refresh(test_user)
    assert test_user.referral_code == stats["referral_code"]


@pytest.mark.asyncio
async def test_get_referral_stats_zero_referrals(test_db, test_user):
    """Test get_referral_stats returns zeros for user with no referrals."""
    # Act
    stats = await get_referral_stats(test_user.id, test_db)

    # Assert
    assert stats["total_referrals"] == 0
    assert stats["pending_referrals"] == 0
    assert stats["total_credits"] == 0


@pytest.mark.asyncio
async def test_get_referral_stats_nonexistent_user(test_db):
    """Test get_referral_stats raises ValueError for nonexistent user."""
    # Act & Assert
    with pytest.raises(ValueError, match="User 99999 not found"):
        await get_referral_stats(99999, test_db)


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_referral_code_case_sensitivity(test_db, test_user):
    """Test referral codes are case-sensitive in validation."""
    # Arrange
    code = "AbCd1234"
    test_user.referral_code = code
    await test_db.commit()

    # Act
    result_exact = await validate_referral_code(code, test_db)
    result_lower = await validate_referral_code(code.lower(), test_db)

    # Assert
    assert result_exact is not None
    assert result_lower is None


@pytest.mark.asyncio
async def test_multiple_referrals_from_same_referrer(test_db, test_user):
    """Test user can refer multiple people."""
    # Arrange
    emails = ["ref1@example.com", "ref2@example.com", "ref3@example.com"]

    # Act
    for i, email in enumerate(emails):
        referral = await create_referral(
            referrer_id=test_user.id,
            referee_email=email,
            payment_intent_id=f"pi_multi_{i}",
            course_id=None,
            db=test_db,
        )
        assert referral is not None

    # Assert
    stats = await get_referral_stats(test_user.id, test_db)
    assert stats["total_referrals"] == 3


@pytest.mark.asyncio
async def test_referral_status_transitions(test_db, test_user):
    """Test referral status transitions: pending -> confirmed -> credited."""
    # Arrange
    referral = Referral(
        referrer_id=test_user.id,
        referee_email="status@example.com",
        stripe_payment_intent_id="pi_status",
        status="pending",
        created_at=datetime.now(UTC),
    )
    test_db.add(referral)
    await test_db.commit()
    await test_db.refresh(referral)

    # Act & Assert - pending -> confirmed
    assert referral.status == "pending"
    await confirm_referral(referral.id, test_db)
    await test_db.refresh(referral)
    assert referral.status == "confirmed"

    # Act & Assert - confirmed -> credited
    await apply_referral_credit(test_user.id, 500, referral.id, test_db)
    await test_db.refresh(referral)
    assert referral.status == "credited"
