import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from db.models import Base
from services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    get_user_experience
)
from models.schemas import UserCreate


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_with_experience_profile(db_session):
    """Test create user with experience profile"""
    user_data = UserCreate(
        email="test@example.com",
        experience_level="Beginner",
        background="Computer Science student",
        goals="Learn AI fundamentals"
    )

    user = await create_user(user_data, db_session)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.experience is not None
    assert user.experience.experience_level == "Beginner"
    assert user.experience.background == "Computer Science student"
    assert user.experience.goals == "Learn AI fundamentals"


@pytest.mark.asyncio
async def test_get_user_by_email(db_session):
    """Test get user by email"""
    # Create a user first
    user_data = UserCreate(
        email="findme@example.com",
        experience_level="Intermediate",
        background="Software engineer",
        goals="Advanced ML techniques"
    )
    created_user = await create_user(user_data, db_session)

    # Retrieve by email
    found_user = await get_user_by_email("findme@example.com", db_session)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "findme@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session):
    """Test get user by email when user doesn't exist"""
    found_user = await get_user_by_email("nonexistent@example.com", db_session)

    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_id(db_session):
    """Test get user by ID"""
    # Create a user first
    user_data = UserCreate(
        email="findbyid@example.com",
        experience_level="Advanced",
        background="AI researcher",
        goals="Contribute to research"
    )
    created_user = await create_user(user_data, db_session)

    # Retrieve by ID
    found_user = await get_user_by_id(created_user.id, db_session)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "findbyid@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session):
    """Test get user by ID when user doesn't exist"""
    found_user = await get_user_by_id(99999, db_session)

    assert found_user is None


@pytest.mark.asyncio
async def test_update_last_login_timestamp(db_session):
    """Test update last login timestamp"""
    # Create a user first
    user_data = UserCreate(
        email="logintest@example.com",
        experience_level="Beginner"
    )
    created_user = await create_user(user_data, db_session)

    assert created_user.last_login is None

    # Update last login
    await update_last_login(created_user.id, db_session)

    # Verify update
    updated_user = await get_user_by_id(created_user.id, db_session)
    assert updated_user.last_login is not None
    assert isinstance(updated_user.last_login, datetime)


@pytest.mark.asyncio
async def test_update_last_login_nonexistent_user(db_session):
    """Test update last login for nonexistent user"""
    # Should not raise error, just silently do nothing
    await update_last_login(99999, db_session)


@pytest.mark.asyncio
async def test_get_user_experience_profile(db_session):
    """Test get user experience profile"""
    # Create a user with experience
    user_data = UserCreate(
        email="experience@example.com",
        experience_level="Intermediate",
        background="Data scientist",
        goals="Deep learning mastery"
    )
    created_user = await create_user(user_data, db_session)

    # Retrieve experience profile
    experience = await get_user_experience(created_user.id, db_session)

    assert experience is not None
    assert experience.user_id == created_user.id
    assert experience.experience_level == "Intermediate"
    assert experience.background == "Data scientist"
    assert experience.goals == "Deep learning mastery"


@pytest.mark.asyncio
async def test_get_user_experience_nonexistent_user(db_session):
    """Test get user experience for nonexistent user"""
    experience = await get_user_experience(99999, db_session)

    assert experience is None


@pytest.mark.asyncio
async def test_create_user_empty_email(db_session):
    """Test edge case: empty email in registration"""
    with pytest.raises(Exception):  # Pydantic validation should fail
        UserCreate(
            email="",
            experience_level="Beginner"
        )


@pytest.mark.asyncio
async def test_create_user_invalid_email_format(db_session):
    """Test edge case: invalid email format"""
    with pytest.raises(Exception):  # Pydantic validation should fail
        UserCreate(
            email="not-an-email",
            experience_level="Beginner"
        )


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session):
    """Test edge case: duplicate user registration attempts"""
    user_data = UserCreate(
        email="duplicate@example.com",
        experience_level="Beginner"
    )

    # Create first user
    await create_user(user_data, db_session)

    # Attempt to create duplicate
    with pytest.raises(Exception):  # Should raise integrity error
        await create_user(user_data, db_session)


@pytest.mark.asyncio
async def test_create_user_very_long_text_fields(db_session):
    """Test edge case: very long text in experience assessment fields"""
    very_long_text = "A" * 10000  # 10k characters

    user_data = UserCreate(
        email="longtext@example.com",
        experience_level="Advanced",
        background=very_long_text,
        goals=very_long_text
    )

    user = await create_user(user_data, db_session)

    assert user.id is not None
    assert len(user.experience.background) == 10000
    assert len(user.experience.goals) == 10000
