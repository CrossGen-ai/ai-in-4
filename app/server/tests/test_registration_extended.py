"""
Comprehensive tests for extended registration form functionality.
Tests all new fields, validations, character limits, and conditional logic.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from db.models import User, UserExperience


# Base valid registration data with all required fields
VALID_REGISTRATION_DATA = {
    "email": "test@example.com",
    "name": "John Doe",
    "employment_status": "Employed full-time",
    "primary_use_context": "Work/Professional tasks",
    "tried_ai_before": True,
    "ai_tools_used": ["ChatGPT", "Claude"],
    "usage_frequency": "Daily",
    "comfort_level": 3,
    "goals": [
        "Writing/content creation",
        "Research and information gathering",
        "Coding/technical tasks"
    ],
    "learning_preference": "Hands-on practice with examples"
}


@pytest.mark.asyncio
async def test_register_with_all_required_fields_only(test_db: AsyncSession):
    """Test successful registration with only required fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=VALID_REGISTRATION_DATA)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_with_all_fields_including_optional(test_db: AsyncSession):
    """Test successful registration with all fields (required + optional)."""
    full_data = {
        **VALID_REGISTRATION_DATA,
        "email": "fulltest@example.com",
        "employment_status_other": None,
        "industry": "Technology",
        "role": "Software Engineer",
        "challenges": ["Writing effective prompts", "Understanding what AI can/can't do"],
        "additional_comments": "Looking forward to learning more about AI!",
        "experience_level": "Intermediate",  # Legacy field
        "background": "Have some coding experience"  # Legacy field
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=full_data)

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "fulltest@example.com"


@pytest.mark.asyncio
async def test_register_missing_required_field_name(test_db: AsyncSession):
    """Test validation failure for missing name field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "noname@example.com"}
    del invalid_data["name"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_employment_status(test_db: AsyncSession):
    """Test validation failure for missing employment_status field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "noemp@example.com"}
    del invalid_data["employment_status"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_primary_use_context(test_db: AsyncSession):
    """Test validation failure for missing primary_use_context field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "nouse@example.com"}
    del invalid_data["primary_use_context"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_tried_ai_before(test_db: AsyncSession):
    """Test validation failure for missing tried_ai_before field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "notried@example.com"}
    del invalid_data["tried_ai_before"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_usage_frequency(test_db: AsyncSession):
    """Test validation failure for missing usage_frequency field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "nofreq@example.com"}
    del invalid_data["usage_frequency"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_comfort_level(test_db: AsyncSession):
    """Test validation failure for missing comfort_level field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "nocomfort@example.com"}
    del invalid_data["comfort_level"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_goals(test_db: AsyncSession):
    """Test validation failure for missing goals field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "nogoals@example.com"}
    del invalid_data["goals"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_required_field_learning_preference(test_db: AsyncSession):
    """Test validation failure for missing learning_preference field."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "nopref@example.com"}
    del invalid_data["learning_preference"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_format(test_db: AsyncSession):
    """Test email format validation."""
    invalid_data = {**VALID_REGISTRATION_DATA, "email": "not-an-email"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_name_too_long(test_db: AsyncSession):
    """Test name character limit enforcement (100 chars)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "longname@example.com",
        "name": "A" * 101  # 101 characters, exceeds 100 limit
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_email_too_long(test_db: AsyncSession):
    """Test email character limit enforcement (150 chars)."""
    # Create email that exceeds 150 chars
    long_local_part = "a" * 140
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": f"{long_local_part}@example.com"  # > 150 chars
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_employment_status_other_too_long(test_db: AsyncSession):
    """Test employment_status_other character limit enforcement (50 chars)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "longemp@example.com",
        "employment_status": "Other",
        "employment_status_other": "A" * 51  # 51 characters, exceeds 50 limit
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_industry_too_long(test_db: AsyncSession):
    """Test industry character limit enforcement (100 chars)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "longind@example.com",
        "industry": "A" * 101  # 101 characters, exceeds 100 limit
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_role_too_long(test_db: AsyncSession):
    """Test role character limit enforcement (100 chars)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "longrole@example.com",
        "role": "A" * 101  # 101 characters, exceeds 100 limit
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_additional_comments_too_long(test_db: AsyncSession):
    """Test additional_comments character limit enforcement (500 chars)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "longcomments@example.com",
        "additional_comments": "A" * 501  # 501 characters, exceeds 500 limit
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_goals_less_than_three(test_db: AsyncSession):
    """Test goals validation requires exactly 3 items (test with 2)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "twogoals@example.com",
        "goals": ["Writing/content creation", "Research and information gathering"]  # Only 2 goals
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_goals_more_than_three(test_db: AsyncSession):
    """Test goals validation requires exactly 3 items (test with 4)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "fourgoals@example.com",
        "goals": [
            "Writing/content creation",
            "Research and information gathering",
            "Coding/technical tasks",
            "Data analysis"  # 4th goal
        ]
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_comfort_level_below_range(test_db: AsyncSession):
    """Test comfort_level validation (must be 1-5, test 0)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "lowcomfort@example.com",
        "comfort_level": 0  # Below valid range
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_comfort_level_above_range(test_db: AsyncSession):
    """Test comfort_level validation (must be 1-5, test 6)."""
    invalid_data = {
        **VALID_REGISTRATION_DATA,
        "email": "highcomfort@example.com",
        "comfort_level": 6  # Above valid range
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_json_arrays_store_correctly(test_db: AsyncSession):
    """Test JSON array fields properly store and retrieve."""
    test_data = {
        **VALID_REGISTRATION_DATA,
        "email": "jsontest@example.com",
        "ai_tools_used": ["ChatGPT", "Claude", "Gemini"],
        "goals": ["Writing/content creation", "Data analysis", "Learning new skills"],
        "challenges": ["Writing effective prompts", "Cost of AI tools"]
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=test_data)

        assert response.status_code == 201

        # Verify data was stored correctly by querying the database
        from sqlalchemy import select
        result = await test_db.execute(
            select(UserExperience).join(User).where(User.email == "jsontest@example.com")
        )
        experience = result.scalar_one_or_none()

        assert experience is not None
        assert experience.ai_tools_used == ["ChatGPT", "Claude", "Gemini"]
        assert experience.goals == ["Writing/content creation", "Data analysis", "Learning new skills"]
        assert experience.challenges == ["Writing effective prompts", "Cost of AI tools"]


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(test_db: AsyncSession):
    """Test that duplicate email addresses are rejected."""
    # First registration
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json={
            **VALID_REGISTRATION_DATA,
            "email": "duplicate@example.com"
        })
        assert response.status_code == 201

        # Attempt duplicate registration
        response = await client.post("/api/auth/register", json={
            **VALID_REGISTRATION_DATA,
            "email": "duplicate@example.com"
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_with_employment_other_and_conditional_field(test_db: AsyncSession):
    """Test employment status 'Other' with conditional text field."""
    test_data = {
        **VALID_REGISTRATION_DATA,
        "email": "empother@example.com",
        "employment_status": "Other",
        "employment_status_other": "Consultant"
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=test_data)

        assert response.status_code == 201


@pytest.mark.asyncio
async def test_register_tried_ai_false_with_no_tools(test_db: AsyncSession):
    """Test tried_ai_before=False without ai_tools_used."""
    test_data = {
        **VALID_REGISTRATION_DATA,
        "email": "noai@example.com",
        "tried_ai_before": False,
        "ai_tools_used": None  # or empty list
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=test_data)

        assert response.status_code == 201


@pytest.mark.asyncio
async def test_register_all_comfort_levels_valid(test_db: AsyncSession):
    """Test that all comfort levels 1-5 are valid."""
    for level in range(1, 6):
        test_data = {
            **VALID_REGISTRATION_DATA,
            "email": f"comfort{level}@example.com",
            "comfort_level": level
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/auth/register", json=test_data)

            assert response.status_code == 201, f"Comfort level {level} should be valid"


@pytest.mark.asyncio
async def test_register_challenges_unlimited_selections(test_db: AsyncSession):
    """Test that challenges field allows unlimited selections."""
    test_data = {
        **VALID_REGISTRATION_DATA,
        "email": "manychallenges@example.com",
        "challenges": [
            "Don't know where to start",
            "Understanding what AI can/can't do",
            "Writing effective prompts",
            "Knowing which tool to use when",
            "Integrating AI into my workflow",
            "Concerns about accuracy/reliability",
            "Privacy/security concerns",
            "Cost of AI tools"
        ]  # 8 challenges - should be allowed
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=test_data)

        assert response.status_code == 201
