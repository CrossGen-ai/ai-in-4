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

    # Create experience profile with all new extended fields
    experience = UserExperience(
        user_id=user.id,
        # Legacy fields (for backward compatibility)
        experience_level=user_data.experience_level,
        background=user_data.background,
        # New extended registration fields
        name=user_data.name,
        employment_status=user_data.employment_status,
        employment_status_other=user_data.employment_status_other,
        industry=user_data.industry,
        role=user_data.role,
        primary_use_context=user_data.primary_use_context,
        tried_ai_before=user_data.tried_ai_before,
        ai_tools_used=user_data.ai_tools_used,
        usage_frequency=user_data.usage_frequency,
        comfort_level=user_data.comfort_level,
        goals=user_data.goals,  # JSON array field
        challenges=user_data.challenges,
        learning_preference=user_data.learning_preference,
        additional_comments=user_data.additional_comments
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
