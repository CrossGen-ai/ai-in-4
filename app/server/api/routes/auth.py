from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import User
from models.schemas import (
    UserCreate,
    MagicLinkRequest,
    MagicLinkValidate,
    AuthResponse,
    UserResponse,
)
from services.user_service import create_user, get_user_by_email
from services.magic_link import generate_magic_link, validate_magic_link, send_magic_link_email
from core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with experience assessment and send magic link."""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create user
    user = await create_user(user_data, db)

    # Generate and send magic link
    try:
        magic_link_url = await generate_magic_link(user.email, db)
        await send_magic_link_email(user.email, magic_link_url)
    except Exception as e:
        logger.error(f"Error generating magic link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating magic link"
        )

    # For the response, we'll use the magic link token as access token temporarily
    # In a real app, you'd generate a proper JWT token here
    token = magic_link_url.split("token=")[-1]

    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@router.post("/magic-link", status_code=status.HTTP_200_OK)
async def request_magic_link(
    request: MagicLinkRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate and send magic link for existing user."""
    user = await get_user_by_email(request.email, db)
    if not user:
        # Don't reveal if user exists or not for security
        return {"message": "If the email exists, a magic link has been sent"}

    try:
        magic_link_url = await generate_magic_link(user.email, db)
        await send_magic_link_email(user.email, magic_link_url)
    except Exception as e:
        logger.error(f"Error generating magic link: {str(e)}")
        # Don't reveal error to user
        pass

    return {"message": "If the email exists, a magic link has been sent"}


@router.post("/validate", response_model=AuthResponse)
async def validate_token(
    validation: MagicLinkValidate,
    db: AsyncSession = Depends(get_db)
):
    """Validate magic link token and return auth response."""
    user, session_token = await validate_magic_link(validation.token, db)

    if not user or not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )

    return AuthResponse(
        access_token=session_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side will clear token)."""
    return {"message": "Logged out successfully"}


@router.get("/dev-users")
async def get_dev_users(db: AsyncSession = Depends(get_db)):
    """Get list of users for dev quick login (only in dev mode)."""
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not available in production"
        )

    result = await db.execute(select(User))
    users = result.scalars().all()

    return [UserResponse.model_validate(user) for user in users]


@router.post("/dev-login", response_model=AuthResponse)
async def dev_login(
    request: MagicLinkRequest,
    db: AsyncSession = Depends(get_db)
):
    """Instant login for dev mode - bypasses magic link flow."""
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not available in production"
        )

    user = await get_user_by_email(request.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update last login
    from datetime import datetime, UTC
    user.last_login = datetime.now(UTC)
    await db.commit()

    # Generate session token using the same serializer as magic_link service
    from services.magic_link import serializer
    session_token = serializer.dumps({"user_id": user.id, "email": user.email}, salt="session")

    print(f"[DEV-LOGIN] User: {user.email}, Token: {session_token[:80]}", flush=True)
    logger.info(f"Dev login successful for user: {user.email}")
    logger.info(f"Generated token (first 50 chars): {session_token[:50]}...")

    return AuthResponse(
        access_token=session_token,
        user=UserResponse.model_validate(user)
    )
