from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User, MagicLink
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Serializer for generating tokens
serializer = URLSafeTimedSerializer(settings.MAGIC_LINK_SECRET)


async def generate_magic_link(email: str, db: AsyncSession) -> str:
    """Generate a magic link token for the given email."""
    # Create a secure token
    token = serializer.dumps(email, salt="magic-link")

    # Get user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    # Calculate expiry
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.MAGIC_LINK_EXPIRY_MINUTES)

    # Store magic link in database
    magic_link = MagicLink(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        used=False
    )
    db.add(magic_link)
    await db.commit()

    # Construct magic link URL
    magic_link_url = f"{settings.FRONTEND_URL}/login?token={token}"

    return magic_link_url


async def validate_magic_link(token: str, db: AsyncSession) -> tuple[User | None, str | None]:
    """Validate a magic link token and return the associated user and a session token."""
    try:
        # Verify token signature and extract email
        serializer.loads(
            token,
            salt="magic-link",
            max_age=settings.MAGIC_LINK_EXPIRY_MINUTES * 60  # Convert to seconds
        )

        # Get magic link from database
        result = await db.execute(
            select(MagicLink).where(MagicLink.token == token)
        )
        magic_link = result.scalar_one_or_none()

        if not magic_link:
            logger.warning(f"Magic link token not found in database: {token[:10]}...")
            return None, None

        # Check if already used
        if magic_link.used:
            logger.warning(f"Magic link already used for user {magic_link.user_id}")
            return None, None

        # Check if expired
        if datetime.now(UTC) > magic_link.expires_at:
            logger.warning(f"Magic link expired for user {magic_link.user_id}")
            return None, None

        # Mark as used
        magic_link.used = True
        await db.commit()

        # Get user
        result = await db.execute(select(User).where(User.id == magic_link.user_id))
        user = result.scalar_one_or_none()

        if user:
            # Update last login
            user.last_login = datetime.now(UTC)
            await db.commit()

            # Generate a long-lived session token
            session_token = serializer.dumps({"user_id": user.id, "email": user.email}, salt="session")
            return user, session_token

        return None, None

    except SignatureExpired:
        logger.warning("Magic link token signature expired")
        return None, None
    except BadSignature:
        logger.warning("Invalid magic link token signature")
        return None, None
    except Exception as e:
        logger.error(f"Error validating magic link: {str(e)}")
        return None, None


async def validate_session_token(token: str, db: AsyncSession) -> User | None:
    """Validate a session token and return the associated user."""
    try:
        print(f"[VALIDATE] Received token: {token[:80]}", flush=True)
        logger.info(f"Validating token (first 50 chars): {token[:50] if len(token) > 50 else token}...")
        # Verify token signature and extract user data
        data = serializer.loads(token, salt="session")
        print(f"[VALIDATE] Token valid! User ID: {data.get('user_id')}", flush=True)
        user_id = data.get("user_id")

        if not user_id:
            return None

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        return user

    except SignatureExpired:
        logger.warning("Session token expired")
        return None
    except BadSignature:
        logger.warning("Invalid session token signature")
        return None
    except Exception as e:
        logger.error(f"Error validating session token: {str(e)}")
        return None


async def send_magic_link_email(email: str, magic_link: str):
    """Send magic link email (or log to console in dev mode)."""
    if settings.DEV_MODE:
        logger.info("=" * 80)
        logger.info("MAGIC LINK EMAIL (Development Mode)")
        logger.info("=" * 80)
        logger.info(f"To: {email}")
        logger.info("Subject: Your Magic Link for AI Course Platform")
        logger.info("")
        logger.info("Click the link below to log in:")
        logger.info(f"{magic_link}")
        logger.info("")
        logger.info(f"This link will expire in {settings.MAGIC_LINK_EXPIRY_MINUTES} minutes.")
        logger.info("=" * 80)
    else:
        # TODO: Implement actual email sending via SMTP
        # For production, use a library like aiosmtplib or a service like SendGrid
        logger.warning("Email sending not implemented for production mode")
        pass
