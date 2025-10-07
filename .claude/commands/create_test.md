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
    """Test description: what and why"""
    # Arrange
    test_data = {...}

    # Act
    result = await function_to_test(test_data, test_db)

    # Assert
    assert result.expected_field == expected_value

def test_function_error_case():
    """Test error handling"""
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
