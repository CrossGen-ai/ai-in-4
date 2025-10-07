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

## How This Knowledge Base Works

1. **Generic Commands**: Slash commands like `/create_test`, `/test_doctor`, `/validate_test` are framework-agnostic
2. **Specific Knowledge**: This KB contains stack-specific patterns that work for THIS codebase
3. **Learning Loop**: ADW test phase automatically updates this KB when new patterns are discovered
4. **Continuous Improvement**: The more tests fail and get fixed, the smarter the system becomes

## Adding New Patterns

When you discover a new failure pattern:

1. Create a new file in `failure_patterns/` with pattern ID as filename
2. Use the template structure (see existing patterns)
3. Update the frequency tracker table above
4. Link from relevant stack guides

## Metrics

- **Total Patterns Documented**: 5
- **Auto-Fix Success Rate**: TBD
- **Pattern Reoccurrence Rate**: TBD
- **KB Coverage**: Growing

Last Updated: 2025-10-06
