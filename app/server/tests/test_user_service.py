import pytest
from datetime import datetime
from services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    get_user_experience
)
from models.schemas import UserCreate


def create_valid_user_data(email: str, **overrides):
    """Helper to create valid UserCreate data with all required fields."""
    defaults = {
        "email": email,
        "name": "Test User",
        "employment_status": "Student",
        "primary_use_context": "Educational purposes",
        "tried_ai_before": True,
        "usage_frequency": "Weekly",
        "comfort_level": 3,
        "goals": ["Learning new skills", "Personal productivity/organization", "Research and information gathering"],
        "learning_preference": "Hands-on practice with examples",
        "experience_level": "Beginner",
    }
    defaults.update(overrides)
    return UserCreate(**defaults)


@pytest.mark.asyncio
async def test_create_user_with_experience_profile(test_db):
    """Test create user with experience profile"""
    user_data = create_valid_user_data(
        "test@example.com",
        background="Computer Science student"
    )

    user = await create_user(user_data, test_db)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True

    # Query experience separately to avoid lazy-load issues
    experience = await get_user_experience(user.id, test_db)
    assert experience is not None
    assert experience.name == "Test User"
    assert experience.background == "Computer Science student"


@pytest.mark.asyncio
async def test_get_user_by_email(test_db):
    """Test get user by email"""
    # Create a user first
    user_data = create_valid_user_data("findme@example.com")
    created_user = await create_user(user_data, test_db)

    # Retrieve by email
    found_user = await get_user_by_email("findme@example.com", test_db)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "findme@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(test_db):
    """Test get user by email when user doesn't exist"""
    found_user = await get_user_by_email("nonexistent@example.com", test_db)

    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_id(test_db):
    """Test get user by ID"""
    # Create a user first
    user_data = create_valid_user_data("findbyid@example.com")
    created_user = await create_user(user_data, test_db)

    # Retrieve by ID
    found_user = await get_user_by_id(created_user.id, test_db)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "findbyid@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(test_db):
    """Test get user by ID when user doesn't exist"""
    found_user = await get_user_by_id(99999, test_db)

    assert found_user is None


@pytest.mark.asyncio
async def test_update_last_login_timestamp(test_db):
    """Test update last login timestamp"""
    # Create a user first
    user_data = create_valid_user_data("logintest@example.com")
    created_user = await create_user(user_data, test_db)

    assert created_user.last_login is None

    # Update last login
    await update_last_login(created_user.id, test_db)

    # Verify update
    updated_user = await get_user_by_id(created_user.id, test_db)
    assert updated_user.last_login is not None
    assert isinstance(updated_user.last_login, datetime)


@pytest.mark.asyncio
async def test_update_last_login_nonexistent_user(test_db):
    """Test update last login for nonexistent user"""
    # Should not raise error, just silently do nothing
    await update_last_login(99999, test_db)


@pytest.mark.asyncio
async def test_get_user_experience_profile(test_db):
    """Test get user experience profile"""
    # Create a user with experience
    user_data = create_valid_user_data("experience@example.com")
    created_user = await create_user(user_data, test_db)

    # Retrieve experience profile
    experience = await get_user_experience(created_user.id, test_db)

    assert experience is not None
    assert experience.user_id == created_user.id
    assert experience.name == "Test User"
    assert experience.goals is not None


@pytest.mark.asyncio
async def test_get_user_experience_nonexistent_user(test_db):
    """Test get user experience for nonexistent user"""
    experience = await get_user_experience(99999, test_db)

    assert experience is None


@pytest.mark.asyncio
async def test_create_user_empty_email(test_db):
    """Test edge case: empty email in registration"""
    with pytest.raises(Exception):  # Pydantic validation should fail
        UserCreate(
            email="",
            experience_level="Beginner"
        )


@pytest.mark.asyncio
async def test_create_user_invalid_email_format(test_db):
    """Test edge case: invalid email format"""
    with pytest.raises(Exception):  # Pydantic validation should fail
        UserCreate(
            email="not-an-email",
            experience_level="Beginner"
        )


@pytest.mark.asyncio
async def test_create_user_duplicate_email(test_db):
    """Test edge case: duplicate user registration attempts"""
    user_data = create_valid_user_data("duplicate@example.com")

    # Create first user
    await create_user(user_data, test_db)

    # Attempt to create duplicate
    with pytest.raises(Exception):  # Should raise integrity error
        await create_user(user_data, test_db)


@pytest.mark.asyncio
async def test_create_user_very_long_text_fields(test_db):
    """Test edge case: very long text in experience assessment fields"""
    very_long_text = "A" * 10000  # 10k characters

    user_data = create_valid_user_data("longtext@example.com", background=very_long_text)

    user = await create_user(user_data, test_db)

    assert user.id is not None

    # Query experience separately to avoid lazy-load issues
    experience = await get_user_experience(user.id, test_db)
    assert len(experience.background) == 10000
    assert len(experience.goals) == 3  # Goals is now an array with 3 items
