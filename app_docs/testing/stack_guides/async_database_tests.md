# Async Database Testing Patterns

**Stack:** FastAPI + SQLAlchemy Async + SQLite + Pytest-AsyncIO
**Last Updated:** 2025-10-06

## Critical Requirements

### ❌ NEVER: In-Memory Database with Async
```python
# BREAKS - Each async connection gets isolated :memory: DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

### ✅ ALWAYS: File-Based Test Database
```python
# WORKS - Shared database across async connections
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)
```

**Why:** SQLite :memory: creates per-connection isolated databases. With async,
each await creates new connection → can't see tables created in setup.

**Evidence:** tests/conftest.py:15-20

---

## Fixture Design Pattern

### Setup/Teardown Lifecycle
```python
@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def test_db(setup_database):
    """Get test database session."""
    async with TestSessionLocal() as session:
        yield session
    # Session auto-closed by async context manager - NO explicit close()
```

**Anti-Pattern:** Double-closing sessions
```python
# ❌ CAUSES "cannot operate on a closed database"
async with TestSessionLocal() as session:
    yield session
    await session.close()  # Already closed by context manager!
```

**Evidence:** tests/conftest.py:26-34

---

## Relationship Loading Strategies

### ❌ NEVER: Lazy-Load Relationships Outside Session
```python
async def test_user(test_db):
    user = await create_user(user_data, test_db)
    # ❌ GREENLET ERROR - lazy-load outside session context
    assert user.experience.background == "test"
```

### ✅ ALWAYS: Query Separately or Eager Load
```python
async def test_user(test_db):
    user = await create_user(user_data, test_db)

    # Option 1: Query relationship separately
    experience = await get_user_experience(user.id, test_db)
    assert experience.background == "test"

    # Option 2: Refresh to load relationships (if needed)
    await test_db.refresh(user)
    # Now user.experience is loaded
```

**Why:** SQLAlchemy async uses greenlets. Lazy-load triggers DB call outside
greenlet context → MissingGreenlet exception.

**Evidence:** tests/test_user_service.py:23-34

---

## DateTime Handling with SQLite

### The Problem
SQLite doesn't preserve timezone info. Storing `datetime.now(UTC)` loses tzinfo on retrieval.

### ❌ FAILS: Timezone-Aware Comparison
```python
# In service
if datetime.now(UTC) > magic_link.expires_at:  # ❌ naive vs aware comparison

# In test
magic_link = MagicLink(
    expires_at=datetime.now(UTC) + timedelta(minutes=15)  # Stored as naive
)
```

### ✅ WORKS: Consistent Naive or Mock
```python
# Option 1: Use naive datetimes consistently
now = datetime.now()  # No UTC
expires_at = now + timedelta(minutes=15)

# Option 2: Mock datetime in service
from unittest.mock import patch
with patch('services.magic_link.datetime') as mock_dt:
    mock_dt.now.return_value = naive_datetime
    # Test proceeds
```

**Evidence:** tests/test_auth.py:134-157

---

## Test Database Cleanup

### Auto-cleanup per test (recommended)
Handled by `autouse=True` fixture - tables dropped after each test.

### Manual cleanup if needed
```python
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    # After all tests
    test_db_path = Path("./test.db")
    if test_db_path.exists():
        test_db_path.unlink()
```

---

## Quick Reference Checklist

- [ ] Using file-based test DB (not :memory:)
- [ ] Fixtures have explicit dependency chain (setup_database → test_db → test_user)
- [ ] No explicit `await session.close()` (context manager handles it)
- [ ] Relationships queried separately or eager-loaded
- [ ] DateTime comparisons use consistent naive/aware strategy
- [ ] Test DB file cleaned up in CI/CD

**Related Patterns:**
- [Database Session Lifecycle](../failure_patterns/database_session_lifecycle.md)
- [Greenlet Errors](../failure_patterns/greenlet_errors.md)
- [DateTime SQLite Issues](../failure_patterns/datetime_sqlite_timezone.md)
