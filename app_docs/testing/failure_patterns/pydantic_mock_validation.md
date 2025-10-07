# Pydantic Validation Failures with Mocks

**Pattern ID:** `pydantic-mock-fail`
**Frequency:** 2 occurrences (2025-10-06)
**Stack:** Pydantic v2 + unittest.mock + FastAPI

## Error Signature

```
pydantic_core._pydantic_core.ValidationError: 1 validation error
  Input should be a valid string [type=string_type, input_value=<AsyncMock ...>, input_type=AsyncMock]
```

## Root Cause

Pydantic validates response models strictly. Mock objects (Mock, AsyncMock, MagicMock)
fail type validation because they're not the expected type (str, int, model, etc.).

## Common Triggers

1. **Returning AsyncMock when Pydantic expects a model**
2. **Mocking service functions that return to Pydantic-validated routes**
3. **Setting mock attributes instead of creating real model instances**

## Fix Pattern

### Before (Fails)
```python
from unittest.mock import AsyncMock

# ❌ WRONG - AsyncMock fails Pydantic validation
mock_experience = AsyncMock()
mock_experience.background = "Software Engineering"
mock_get_experience.return_value = mock_experience

# When FastAPI validates response:
# ValidationError: Input should be a valid string, got AsyncMock
```

### After (Works)
```python
from db.models import UserExperience
from datetime import datetime, UTC

# ✅ CORRECT - Real model instance passes validation
mock_experience = UserExperience(
    id=1,
    user_id=1,
    experience_level="Intermediate",
    background="Software Engineering",
    goals="Build AI applications",
    created_at=datetime.now(UTC)
)
mock_get_experience.return_value = mock_experience
```

## When to Use Real Instances

Return real model instances when:
- Mocking service functions called by FastAPI routes
- Route has `response_model` that uses the model
- Pydantic will validate the return value

## When AsyncMock is OK

AsyncMock is fine when:
- Return value is NOT validated by Pydantic
- Mocking internal async functions (not exposed to routes)
- Return value is a primitive type (str, int, bool) set with `return_value`

## Quick Fix Checklist

1. Check if route has `response_model=SomeModel`
2. If yes, mock must return real `SomeModel` instance
3. Create instance with all required fields
4. Use `mock.return_value = real_instance`

## Prevention

- Always check route's `response_model` before mocking
- Import actual model classes for mock return values
- Test with `pytest -v` to catch validation errors early

## Related

- [FastAPI Route Tests](../stack_guides/fastapi_route_tests.md#pydantic-model-mocking)

## Occurrences

1. tests/test_users.py:131 (2025-10-06) - FIXED (UserExperience model)
2. tests/test_users.py:140 (2025-10-06) - FIXED (UserExperience model)
