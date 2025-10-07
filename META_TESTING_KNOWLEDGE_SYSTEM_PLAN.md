# Meta-Testing Knowledge System Implementation Plan

**Date Created:** 2025-10-06
**Purpose:** Build self-improving test quality system that learns from failures
**Key Principle:** Generic slash commands + Specific knowledge base = Reusable intelligence

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Generic Slash Commands                    │
│  /create_test  /test_doctor  /validate_test  /analyze_failures│
│         (Never contain stack-specific knowledge)             │
└─────────────────┬───────────────────────────────────────────┘
                  │ References
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Structured Knowledge Base                       │
│              app_docs/testing/**/*.md                        │
│        (All stack-specific patterns stored here)             │
└─────────────────┬───────────────────────────────────────────┘
                  │ Updates via
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 ADW Test Phase Integration                   │
│           (Auto-learns from failures, updates KB)            │
└─────────────────────────────────────────────────────────────┘
```

**Design Philosophy:**
- Commands are **generic frameworks** (how to think about tests)
- Knowledge base is **specific patterns** (what works in THIS stack)
- ADW becomes the **learning loop** (pattern extraction + KB updates)

---

## Phase 1: Knowledge Base Structure

### 1.1 Create Testing Knowledge Directory

```bash
mkdir -p app_docs/testing/failure_patterns
mkdir -p app_docs/testing/stack_guides
mkdir -p app_docs/testing/best_practices
```

### 1.2 Knowledge Base Index

**File:** `app_docs/testing/README.md`

```markdown
# Testing Knowledge Base

**Purpose:** Stack-specific testing patterns, pitfalls, and solutions.
**Audience:** AI agents creating/fixing tests for this codebase.
**Update Frequency:** After every test failure pattern discovery.

## Quick Navigation

### By Test Type
- [Async Database Tests](./stack_guides/async_database_tests.md)
- [FastAPI Route Tests](./stack_guides/fastapi_route_tests.md)
- [Service Layer Tests](./stack_guides/service_layer_tests.md)
- [Pydantic Model Tests](./stack_guides/pydantic_validation_tests.md)

### By Technology Stack
- [Pytest + AsyncIO](./stack_guides/pytest_asyncio.md)
- [SQLAlchemy Async + SQLite](./stack_guides/sqlalchemy_async_sqlite.md)
- [FastAPI TestClient](./stack_guides/fastapi_testclient.md)

### Common Failure Patterns
- [Greenlet/AsyncIO Errors](./failure_patterns/greenlet_errors.md)
- [Mock Location Mistakes](./failure_patterns/mock_import_paths.md)
- [Pydantic Validation Failures](./failure_patterns/pydantic_mock_validation.md)
- [Database Session Issues](./failure_patterns/database_session_lifecycle.md)
- [Timezone/DateTime Handling](./failure_patterns/datetime_sqlite_timezone.md)

### Best Practices
- [Fixture Dependencies](./best_practices/fixture_design.md)
- [Test Isolation Strategies](./best_practices/test_isolation.md)
- [Mock Object Patterns](./best_practices/mock_patterns.md)

## Pattern Frequency Tracker

| Pattern | Occurrences | Last Seen | Status |
|---------|-------------|-----------|--------|
| mock-import-path | 5 | 2025-10-06 | Documented |
| greenlet-lazy-load | 3 | 2025-10-06 | Documented |
| pydantic-mock-fail | 2 | 2025-10-06 | Documented |
| sqlite-timezone | 2 | 2025-10-06 | Documented |
| memory-db-async | 1 | 2025-10-06 | Documented |

*Updated by: ADW test phase automation*
```

### 1.3 Core Stack Guide: Async Database Tests

**File:** `app_docs/testing/stack_guides/async_database_tests.md`

```markdown
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
```

### 1.4 Core Stack Guide: Mock Patterns

**File:** `app_docs/testing/stack_guides/fastapi_route_tests.md`

```markdown
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
```

### 1.5 Failure Pattern: Greenlet Errors

**File:** `app_docs/testing/failure_patterns/greenlet_errors.md`

```markdown
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
```

---

## Phase 2: Generic Slash Commands

### 2.1 Update /create_test (Keep Generic)

**File:** `.claude/commands/create_test.md`

```markdown
---
description: Create comprehensive test files following best practices
---

You are an expert test creator. Create tests that are maintainable, isolated, and comprehensive.

## Process

1. **Understand Context**
   - Read the module/function to test
   - Identify test boundaries (unit vs integration)
   - Check existing test patterns in tests/

2. **Load Knowledge Base**
   Before writing tests, review:
   - app_docs/testing/README.md (always)
   - Stack-specific guides matching the code under test:
     * Database operations → async_database_tests.md
     * API routes → fastapi_route_tests.md
     * Service functions → service_layer_tests.md
   - Common failure patterns to avoid

3. **Design Test Cases**
   - Happy path (success scenarios)
   - Edge cases (boundaries, empty inputs)
   - Error cases (validation failures, exceptions)
   - Integration points (dependencies, side effects)

4. **Write Tests**
   - Follow patterns from knowledge base
   - Use fixtures from conftest.py
   - Apply stack-specific requirements
   - Include descriptive docstrings

5. **Validate**
   - Run tests: `uv run pytest tests/test_<name>.py -v`
   - Check coverage
   - Verify isolation (tests don't depend on each other)

## Test Structure Template

```python
import pytest
from unittest.mock import patch, AsyncMock

# Import subject under test
from module.path import function_to_test

# Import fixtures if needed (auto-discovered from conftest.py)

@pytest.mark.asyncio  # If testing async
async def test_function_happy_path(test_db):  # Use fixtures
    \"\"\"Test description: what and why\"\"\"
    # Arrange
    test_data = {...}

    # Act
    result = await function_to_test(test_data, test_db)

    # Assert
    assert result.expected_field == expected_value

def test_function_error_case():
    \"\"\"Test error handling\"\"\"
    with pytest.raises(ExpectedException):
        function_to_test(invalid_input)
```

## Quality Checklist

- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] One assertion per test (when possible)
- [ ] Descriptive test names (test_<function>_<scenario>)
- [ ] No hard-coded values (use fixtures/factories)
- [ ] Tests are isolated (no shared state)
- [ ] Stack-specific patterns applied (from knowledge base)

## Output

Create the test file with all test cases. Run pytest to verify they pass.

**NOTE:** This command is framework-agnostic. Stack-specific knowledge lives
in app_docs/testing/. Update KB, not this command, when patterns change.
```

### 2.2 Create /test_doctor Command

**File:** `.claude/commands/test_doctor.md`

```markdown
---
description: Diagnose test failures and suggest fixes based on knowledge base
---

You are a test failure diagnostician. Analyze failures, match patterns, suggest fixes.

## Process

1. **Gather Failure Data**
   - Read pytest output (from user or run pytest)
   - Extract error type, traceback, failing test names
   - Identify affected files

2. **Load Knowledge Base**
   Read pattern guides:
   - app_docs/testing/failure_patterns/*.md
   - app_docs/testing/stack_guides/*.md (for context)

3. **Pattern Matching**
   For each failure:
   - Categorize error type (greenlet, mock, validation, etc.)
   - Match against known patterns in KB
   - Calculate confidence (exact match, similar, unknown)

4. **Generate Diagnosis**
   For each failure, output:
   ```markdown
   ### Test: test_name (file:line)
   **Error Type:** CategoryName
   **Pattern Match:** pattern-id (confidence: high/medium/low)
   **Root Cause:** Brief explanation

   **Fix:**
   \`\`\`python
   # Before (current code)
   problematic_code

   # After (fix)
   fixed_code
   \`\`\`

   **Reference:** app_docs/testing/path/to/pattern.md
   ```

5. **Apply Fixes** (if requested)
   - Use Edit tool to apply suggested changes
   - Re-run tests to verify
   - Report results

6. **Extract New Patterns** (if unknown failure)
   - If confidence < 50%, this is a NEW pattern
   - Document it in failure_patterns/
   - Update pattern frequency tracker

## Output Format

```markdown
# Test Failure Diagnosis Report

**Run:** YYYY-MM-DD HH:MM
**Total Failures:** N
**Known Patterns:** M
**New Patterns:** P

## Failures

[Individual diagnoses as above]

## Summary
- X failures matched known patterns
- Y failures are new (documented in KB)
- Z suggested fixes

## Actions Taken
- Applied fixes to: file1.py, file2.py
- Created new pattern: pattern_name.md
- Updated frequency tracker

## Next Steps
[Recommendations]
```

## Pattern Confidence Scoring

- **High (90%+):** Error message exact match + same context
- **Medium (50-89%):** Similar error, different context
- **Low (<50%):** Error type match only, unknown root cause

## Learning Mode

After successful fix:
1. Update pattern frequency counter
2. Add occurrence to pattern file
3. Update "Last Seen" date
4. If pattern frequency > 5, add to "Common Pitfalls" section

**NOTE:** This command learns from every failure. The more it runs, the smarter it gets.
```

### 2.3 Create /validate_test Command

**File:** `.claude/commands/validate_test.md`

```markdown
---
description: Validate test quality against knowledge base standards
---

You are a test quality validator. Check tests against best practices and stack patterns.

## Process

1. **Read Test File**
   - Load the test file to validate
   - Identify test framework and patterns used

2. **Load Standards**
   - app_docs/testing/best_practices/*.md
   - app_docs/testing/stack_guides/*.md (relevant to test type)

3. **Check Quality Dimensions**

   **A. Structure**
   - [ ] Follows AAA pattern (Arrange, Act, Assert)
   - [ ] One test per function/behavior
   - [ ] Clear test names (test_<what>_<when>_<then>)

   **B. Isolation**
   - [ ] No shared state between tests
   - [ ] Uses fixtures properly
   - [ ] Cleanup after test (if needed)

   **C. Stack Compliance**
   - [ ] Follows async patterns (if applicable)
   - [ ] Mock locations correct (if applicable)
   - [ ] Database handling correct (if applicable)

   **D. Assertions**
   - [ ] Meaningful assertions (not just "assert True")
   - [ ] Error cases tested
   - [ ] Edge cases covered

4. **Score Test Quality**
   Calculate score: (checks_passed / total_checks) * 100

5. **Generate Report**
   ```markdown
   # Test Validation Report: test_file.py

   **Quality Score:** X/100

   ## Strengths
   - Well-structured AAA pattern
   - Good fixture usage

   ## Issues

   ### Critical (Must Fix)
   - Issue 1 (file:line)
     Fix: [specific change]
     Reference: [KB link]

   ### Warnings (Should Fix)
   - Issue 2 (file:line)

   ### Suggestions (Nice to Have)
   - Improvement 1

   ## Stack Compliance
   ✅ Async patterns correct
   ⚠️ Mock import paths need fixing
   ✅ Database fixtures proper

   ## Coverage Analysis
   - Happy paths: 3/3 ✅
   - Error cases: 1/3 ⚠️
   - Edge cases: 0/2 ❌
   ```

6. **Auto-fix** (if requested)
   Apply fixes for critical issues

## Quality Thresholds

- **90-100:** Excellent
- **70-89:** Good
- **50-69:** Needs improvement
- **<50:** Significant issues

**NOTE:** Standards evolve. This command reads from KB, so it stays current.
```

---

## Phase 3: ADW Integration

**Goal:** Integrate test_doctor into BOTH test workflows (standard + ISO)

**Strategy:** Create shared module → Import in both files → No code duplication

### 3.1 Modify Test Workflows (Both Standard & ISO)

**Files to Update:**
- ✅ `adws/adw_test.py` (standard workflow - main repo)
- ✅ `adws/adw_test_iso.py` (ISO workflow - isolated worktree)

**Key Insight:** Both files have identical test execution logic. The only difference is:
- `adw_test.py` runs in main repo directory
- `adw_test_iso.py` runs in isolated worktree with `working_dir` parameter

Apply the same integration to BOTH files.

**Integration Points:**

```python
# Add after test execution (around line 900 in adw_test.py, line 800 in adw_test_iso.py)

async def analyze_test_failures(test_output: str, state: ADWState, logger) -> dict:
    """
    Analyze test failures using /test_doctor and extract patterns.

    Returns:
        dict with diagnosis, fixes applied, new patterns discovered
    """
    logger.info("Analyzing test failures with test_doctor...")

    # Run test_doctor diagnosis
    diagnosis_result = await run_slash_command(
        "/test_doctor",
        context=test_output,
        logger=logger
    )

    # Parse diagnosis
    diagnosis = parse_diagnosis(diagnosis_result)

    # Track metrics
    metrics = {
        "total_failures": diagnosis.get("total_failures", 0),
        "known_patterns": diagnosis.get("known_patterns", 0),
        "new_patterns": diagnosis.get("new_patterns", 0),
        "fixes_applied": 0
    }

    # Apply suggested fixes if high confidence
    for failure in diagnosis.get("failures", []):
        if failure.get("confidence") == "high":
            try:
                apply_fix(failure["fix"])
                metrics["fixes_applied"] += 1
            except Exception as e:
                logger.warning(f"Could not auto-apply fix: {e}")

    # Update knowledge base if new patterns found
    if metrics["new_patterns"] > 0:
        update_knowledge_base(diagnosis.get("new_patterns_data", []), logger)

    # Update pattern frequency tracker
    update_pattern_tracker(diagnosis.get("pattern_matches", []))

    return metrics

# Integrate into test workflow (around line 950 in adw_test.py, line 850 in adw_test_iso.py)

if test_result.returncode != 0:
    logger.warning("Tests failed. Analyzing failures...")

    # Analyze failures
    analysis = await analyze_test_failures(
        test_output=test_result.stdout,
        state=state,
        logger=logger
    )

    logger.info(f"Analysis complete: {analysis}")

    # Re-run tests if fixes applied
    if analysis["fixes_applied"] > 0:
        logger.info(f"Applied {analysis['fixes_applied']} fixes. Re-running tests...")

        # For adw_test_iso.py, pass working_dir parameter
        working_dir = state.get_working_directory() if hasattr(state, 'get_working_directory') else None
        test_result = await run_tests(state, logger, working_dir=working_dir)

        if test_result.returncode == 0:
            logger.info("✅ Tests now passing after auto-fixes!")
        else:
            logger.warning("⚠️ Tests still failing after auto-fixes. Manual intervention needed.")
```

**ISO-Specific Considerations:**

The ISO version operates in isolated worktrees, so ensure:
- Pattern extraction considers worktree path context
- Fixes are applied to correct worktree directory
- Pattern occurrences track which worktree (useful for parallel debugging)

```python
# In test_doctor.py - add worktree awareness

def apply_fix(fix: Dict, working_dir: Optional[str] = None) -> None:
    """Apply fix to correct directory (main repo or worktree)."""
    file_path = fix["file_path"]

    if working_dir:
        # ISO mode - apply to worktree
        full_path = Path(working_dir) / file_path
    else:
        # Standard mode - apply to main repo
        full_path = Path(file_path)

    # Apply the fix...
```

### 3.2 Shared Test Doctor Module

Since both workflows use identical test execution logic, create a SHARED module:

**File:** `adws/adw_modules/test_analysis.py` (new file)

```python
"""
Shared test analysis logic for both standard and ISO workflows.
"""

async def analyze_and_fix_test_failures(
    test_output: str,
    state: ADWState,
    logger,
    working_dir: Optional[str] = None  # None = standard, path = ISO
) -> dict:
    """
    Unified test failure analysis for both workflows.

    Args:
        test_output: Pytest output
        state: ADW state
        logger: Logger instance
        working_dir: None for standard, worktree path for ISO

    Returns:
        Analysis metrics dict
    """
    # Same logic as analyze_test_failures above
    # Just make it working_dir-aware
    ...
```

Then both `adw_test.py` and `adw_test_iso.py` import and call this shared function:

```python
# In adw_test.py (standard)
from adw_modules.test_analysis import analyze_and_fix_test_failures

if test_result.returncode != 0:
    analysis = await analyze_and_fix_test_failures(
        test_output=test_result.stdout,
        state=state,
        logger=logger,
        working_dir=None  # Standard mode - main repo
    )

# In adw_test_iso.py (isolated)
from adw_modules.test_analysis import analyze_and_fix_test_failures

if test_result.returncode != 0:
    working_dir = state.get_working_directory()  # Get worktree path
    analysis = await analyze_and_fix_test_failures(
        test_output=test_result.stdout,
        state=state,
        logger=logger,
        working_dir=working_dir  # ISO mode - worktree path
    )
```

**Why Shared Module?**
- Single source of truth for test analysis logic
- Changes propagate to both workflows automatically
- No duplicate code maintenance
- Worktree handling abstracted cleanly

**Parallel Execution Benefits:**
With ISO workflows, you can:
1. Run 5+ issues in parallel, each in isolated worktree
2. Each gets independent test_doctor analysis
3. Pattern extraction happens concurrently
4. KB updates are thread-safe (file-based)
5. Frequency tracker aggregates across all parallel runs

This means the KB learns 5x faster when running parallel ISO workflows!

### 3.3 Add Pattern Extraction Functions

**File:** `adws/adw_modules/test_doctor.py` (new file)

```python
"""
Test Doctor - Automated test failure diagnosis and pattern extraction.
"""

from pathlib import Path
from datetime import datetime
import json
import re
from typing import Dict, List, Optional

TESTING_KB_PATH = Path("app_docs/testing")
PATTERNS_PATH = TESTING_KB_PATH / "failure_patterns"
TRACKER_FILE = TESTING_KB_PATH / "pattern_frequency.json"


def update_pattern_tracker(pattern_matches: List[Dict]) -> None:
    """Update pattern frequency tracker."""
    tracker = load_tracker()

    for match in pattern_matches:
        pattern_id = match["pattern_id"]

        if pattern_id not in tracker:
            tracker[pattern_id] = {
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": None,
                "status": "active"
            }

        tracker[pattern_id]["count"] += 1
        tracker[pattern_id]["last_seen"] = datetime.now().isoformat()

    save_tracker(tracker)
    update_readme_frequency_table(tracker)


def update_knowledge_base(new_patterns: List[Dict], logger) -> None:
    """Document new failure patterns."""
    for pattern_data in new_patterns:
        pattern_file = PATTERNS_PATH / f"{pattern_data['id']}.md"

        if pattern_file.exists():
            logger.info(f"Pattern {pattern_data['id']} already exists, updating...")
            append_occurrence(pattern_file, pattern_data)
        else:
            logger.info(f"Creating new pattern: {pattern_data['id']}")
            create_pattern_file(pattern_file, pattern_data)


def create_pattern_file(file_path: Path, data: Dict) -> None:
    """Create new pattern documentation."""
    content = f"""# {data['name']}

**Pattern ID:** `{data['id']}`
**Frequency:** 1 occurrence ({datetime.now().strftime('%Y-%m-%d')})
**Stack:** {data.get('stack', 'Unknown')}

## Error Signature

```
{data['error_signature']}
```

## Root Cause

{data['root_cause']}

## Common Triggers

{format_list(data.get('triggers', []))}

## Fix Pattern

### Before (Fails)
```python
{data['before_code']}
```

### After (Works)
```python
{data['after_code']}
```

## Prevention

{format_list(data.get('prevention_tips', []))}

## Related

{format_links(data.get('related_docs', []))}

## Occurrences

1. {data['first_occurrence']} ({datetime.now().strftime('%Y-%m-%d')}) - DISCOVERED
"""
    file_path.write_text(content)


def load_tracker() -> Dict:
    """Load pattern frequency tracker."""
    if TRACKER_FILE.exists():
        return json.loads(TRACKER_FILE.read_text())
    return {}


def save_tracker(tracker: Dict) -> None:
    """Save pattern frequency tracker."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(tracker, indent=2))


# Helper functions...
```

---

## Phase 4: Conditional Docs Integration

### 4.1 Update /conditional_docs

**File:** `.claude/commands/conditional_docs.md`

Add trigger rules:

```markdown
## Testing Documentation Triggers

Load testing KB when:

**Keywords in message:**
- "test", "pytest", "failing", "failure"
- "mock", "fixture", "async test"
- "greenlet", "validation error"

**Files changed:**
- tests/*.py
- conftest.py
- Any file with test_ prefix

**Commands executed:**
- /create_test
- /test_doctor
- /validate_test
- /test

**Docs to load:**
1. app_docs/testing/README.md (always - index)
2. Specific guides based on context:
   - "async" OR "database" → async_database_tests.md
   - "route" OR "api" OR "endpoint" → fastapi_route_tests.md
   - "mock" → fastapi_route_tests.md (mock section)
3. Failure patterns if error keywords present:
   - "greenlet" → greenlet_errors.md
   - "mock" + "not called" → mock_import_paths.md
   - "pydantic" + "validation" → pydantic_mock_validation.md

**Load strategy:**
- Load README index first
- Load 2-3 most relevant guides
- Keep context under 10K tokens
```

---

## Phase 5: Metrics & Evolution

### 5.1 Add KPI Tracking to ADW

Track test quality metrics in agentic KPIs:

```markdown
## Test Quality KPIs

| Metric | Current | Target | Trend |
|--------|---------|--------|-------|
| Test Pass Rate | 100% | 100% | ✅ |
| Pattern Reoccurrence | 5% | <10% | ✅ |
| Auto-Fix Success | 85% | >80% | ✅ |
| KB Coverage | 12 patterns | Growing | 📈 |
| Avg Diagnosis Time | 45s | <60s | ✅ |
| New Pattern Discovery Rate | 0.5/week | - | 📊 |

**Pattern Frequency Top 5:**
1. mock-import-path (5 occurrences)
2. greenlet-lazy-load (3)
3. pydantic-mock-fail (2)
4. sqlite-timezone (2)
5. memory-db-async (1)
```

### 5.2 Self-Improvement Loop

```python
# In adw_document.py - add to documentation phase

async def update_testing_kb_metrics():
    """Update testing KB with latest metrics."""

    # Load pattern tracker
    tracker = load_pattern_tracker()

    # Calculate trend metrics
    metrics = calculate_kb_metrics(tracker)

    # Update README with metrics
    update_readme_metrics(metrics)

    # Identify high-frequency patterns for documentation improvements
    high_freq_patterns = [
        p for p, data in tracker.items()
        if data["count"] >= 5
    ]

    if high_freq_patterns:
        # These patterns need better prevention docs
        logger.info(f"High-frequency patterns detected: {high_freq_patterns}")
        # Could trigger automatic doc enhancement here
```

---

## Implementation Sequence

### Day 1: Foundation (2-3 hours)
1. ✅ Create directory structure
2. ✅ Write README.md index
3. ✅ Document 5 core patterns from today's fixes:
   - async_database_tests.md
   - fastapi_route_tests.md
   - greenlet_errors.md
   - mock_import_paths.md
   - pydantic_mock_validation.md

### Day 2: Commands (2-3 hours)
4. ✅ Update /create_test (add KB references)
5. ✅ Create /test_doctor command
6. ✅ Create /validate_test command

### Day 3: ADW Integration (3-4 hours)
7. ✅ Create shared test_analysis.py module (DRY principle)
8. ✅ Integrate into adw_test.py (standard workflow)
9. ✅ Integrate into adw_test_iso.py (ISO workflow)
10. ✅ Add pattern extraction with worktree awareness
11. ✅ Test both standard and ISO workflows

### Day 4: Conditional Docs (1-2 hours)
11. ✅ Update /conditional_docs triggers
12. ✅ Test KB loading in different scenarios

### Day 5: Metrics & Polish (2-3 hours)
13. ✅ Add KPI tracking
14. ✅ Create pattern frequency tracker
15. ✅ Document the meta-system itself

**Total Effort:** ~10-15 hours
**ROI:** Saves 30+ minutes per test failure + compounds over time

---

## Success Criteria

### Week 1
- [ ] 5 core patterns documented
- [ ] /test_doctor can diagnose 80%+ of failures
- [ ] KB referenced in at least 3 commands

### Month 1
- [ ] 15+ patterns documented
- [ ] Auto-fix success rate >70%
- [ ] Zero repeat failures from same pattern
- [ ] 2+ new patterns discovered and documented

### Month 3
- [ ] Pattern reoccurrence rate <10%
- [ ] Test creation time reduced 40%
- [ ] KB has 25+ patterns
- [ ] Test doctor integrated into CI/CD

---

## Maintenance

### Weekly
- Review pattern frequency tracker
- Update high-frequency pattern docs with prevention tips
- Clean up outdated patterns

### Monthly
- Analyze pattern trends
- Identify gaps in KB coverage
- Update KPIs dashboard
- Review command effectiveness

### Quarterly
- Major KB reorganization if needed
- Archive low-frequency/obsolete patterns
- Publish internal test quality report

---

## Extensibility

This system can extend to:
- **Code review patterns** (app_docs/code_review/)
- **Deployment patterns** (app_docs/deployment/)
- **Performance patterns** (app_docs/performance/)
- **Security patterns** (app_docs/security/)

Same architecture: Generic commands + Specific KB + ADW learning loop.

---

## Notes

- Keep commands GENERIC (they're the framework)
- Keep KB SPECIFIC (it's the knowledge)
- Let ADW be the LEARNING LOOP (it connects them)
- Measure everything (KPIs drive improvement)
- Document failures immediately (capture while fresh)

**Remember:** The goal isn't perfect tests today. It's a system that gets smarter with every failure.
