from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from models.schemas import UserResponse, UserExperienceResponse
from services.user_service import get_user_by_id, get_user_experience
from services.magic_link import validate_session_token

router = APIRouter()


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get current user from authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")

    # Validate session token
    user = await validate_session_token(token, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.get("/me/experience", response_model=UserExperienceResponse)
async def get_current_user_experience(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's experience profile."""
    experience = await get_user_experience(current_user.id, db)

    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience profile not found"
        )

    return UserExperienceResponse.model_validate(experience)
