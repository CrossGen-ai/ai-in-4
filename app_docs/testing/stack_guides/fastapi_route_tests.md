# FastAPI Route Testing Patterns

**Stack:** FastAPI + Dependency Injection + Mocks
**Last Updated:** 2025-10-06

## The Import Path Rule

### Critical Principle: Mock Where Used, Not Where Defined

**Why it matters:** Python imports create references. Mocking at definition point
doesn't affect the imported reference in the module under test.

### ❌ WRONG: Mock at Definition
```python
# Test file
from unittest.mock import patch

with patch('services.magic_link.send_magic_link_email') as mock:
    # This mock is NEVER CALLED because route imports from services
    response = client.post("/api/auth/register", json={...})
```

**File structure:**
```
services/magic_link.py          # Definition
  ↓ imported by
api/routes/auth.py               # Usage
  ↓ called by
tests/test_auth.py               # Test
```

When `auth.py` does `from services.magic_link import send_magic_link_email`,
it creates a LOCAL reference. Patching the original doesn't affect the copy.

### ✅ CORRECT: Mock at Usage Site
```python
with patch('api.routes.auth.send_magic_link_email') as mock:
    # NOW the mock intercepts calls from the route
    response = client.post("/api/auth/register", json={...})
    mock.assert_called_once()
```

**Evidence:** tests/test_auth.py:12,34,94,106

---

## Async Function Mocking

### ❌ WRONG: Regular Mock for Async
```python
with patch('api.routes.users.validate_session_token') as mock:
    mock.return_value = user
    # ❌ Returns Mock object, not awaitable
```

### ✅ CORRECT: AsyncMock with new_callable
```python
from unittest.mock import AsyncMock

with patch('api.routes.users.validate_session_token',
           new_callable=AsyncMock) as mock:
    mock.return_value = user
    # ✅ Returns awaitable coroutine
```

**Why:** Async functions are coroutines. Regular Mock returns Mock object,
not awaitable. FastAPI tries to await it → TypeError.

**Evidence:** tests/test_users.py:80,81,122,123

---

## Pydantic Model Mocking

### ❌ WRONG: Return AsyncMock for Model Validation
```python
mock_experience = AsyncMock()
mock_experience.background = "test"
mock_get_experience.return_value = mock_experience

# ❌ Pydantic validation fails - AsyncMock is not a valid string
```

### ✅ CORRECT: Return Real Model Instance
```python
from db.models import UserExperience
from datetime import datetime, UTC

mock_experience = UserExperience(
    id=1,
    user_id=1,
    experience_level="Intermediate",
    background="Software Engineering",
    goals="Build AI applications",
    created_at=datetime.now(UTC)
)
mock_get_experience.return_value = mock_experience
# ✅ Real model passes Pydantic validation
```

**Why:** Pydantic validates field types. AsyncMock objects fail type validation.
Need real instances with proper types.

**Evidence:** tests/test_users.py:131-140

---

## Dependency Injection Override

FastAPI's dependency injection system requires special handling for testing.

### Global Override Pattern
```python
# conftest.py
from main import app
from db.database import get_db

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
```

This overrides the DB dependency globally for all tests using the TestClient.

**Evidence:** tests/conftest.py:40

---

## Quick Reference Checklist

- [ ] Mocking at usage site (api.routes.X, not services.X)
- [ ] Using AsyncMock with new_callable for async functions
- [ ] Returning real model instances for Pydantic validation
- [ ] Dependency overrides set in conftest.py
- [ ] Mock assertions checking call count/args

**Related Patterns:**
- [Mock Import Paths](../failure_patterns/mock_import_paths.md)
- [Pydantic Mock Validation](../failure_patterns/pydantic_mock_validation.md)
