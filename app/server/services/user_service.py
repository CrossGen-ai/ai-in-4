from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User, UserExperience
from models.schemas import UserCreate
from datetime import datetime, UTC


async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    """Create a new user with experience profile."""
    # Create user
    user = User(
        email=user_data.email,
        is_active=True
    )
    db.add(user)
    await db.flush()  # Flush to get user.id

    # Create experience profile
    experience = UserExperience(
        user_id=user.id,
        experience_level=user_data.experience_level,
        background=user_data.background,
        goals=user_data.goals
    )
    db.add(experience)
    await db.commit()
    await db.refresh(user)

    return user


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_last_login(user_id: int, db: AsyncSession):
    """Update user's last login timestamp."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.last_login = datetime.now(UTC)
        await db.commit()


async def get_user_experience(user_id: int, db: AsyncSession) -> UserExperience | None:
    """Get user's experience profile."""
    result = await db.execute(
        select(UserExperience).where(UserExperience.user_id == user_id)
    )
    return result.scalar_one_or_none()
