# Greenlet/AsyncIO Errors in Tests

**Pattern ID:** `greenlet-lazy-load`
**Frequency:** 3 occurrences (2025-10-06)
**Stack:** SQLAlchemy Async + Pytest

## Error Signature

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here. Was IO attempted in an unexpected place?
```

## Root Cause

SQLAlchemy async uses greenlets to manage async context. Accessing lazy-loaded
relationships outside an active async session triggers DB I/O outside greenlet
context.

## Common Triggers

1. **Accessing relationships after session closed**
2. **Lazy-loading in synchronous test code**
3. **Using `test_db.refresh()` without awaiting**

## Fix Pattern

### Before (Fails)
```python
async def test_create_user_with_experience(test_db):
    user = await create_user(user_data, test_db)
    # ❌ Triggers lazy-load outside session
    assert user.experience.background == "expected"
```

### After (Works)
```python
async def test_create_user_with_experience(test_db):
    user = await create_user(user_data, test_db)
    # ✅ Query separately
    experience = await get_user_experience(user.id, test_db)
    assert experience.background == "expected"
```

## Prevention

- Never access lazy-loaded relationships directly in tests
- Always query relationships via service functions
- Use eager loading if relationship access is critical

## Related

- [Async Database Tests](../stack_guides/async_database_tests.md#relationship-loading-strategies)
- [Database Session Lifecycle](./database_session_lifecycle.md)

## Occurrences

1. tests/test_user_service.py:28 (2025-10-06) - FIXED
2. tests/test_user_service.py:200 (2025-10-06) - FIXED
3. tests/test_users.py:89 (2025-10-06) - FIXED
