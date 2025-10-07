"""Shared test fixtures and configuration."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from main import app
from db.database import get_db, Base
from db.models import User, UserExperience


# Create test database engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Override the get_db dependency for testing."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override the dependency globally
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create a test client for making HTTP requests."""
    return TestClient(app)


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_db():
    """Get test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    test_db.add(user)
    await test_db.flush()

    experience = UserExperience(
        user_id=user.id,
        experience_level="Beginner",
        background="Testing",
        goals="Learn AI",
    )
    test_db.add(experience)
    await test_db.commit()
    await test_db.refresh(user)
    return user
