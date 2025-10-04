# Backend Tests

This directory contains all backend tests for the application.

## Structure

```
tests/
├── __init__.py           # Pytest configuration and fixtures
├── README.md             # This file
├── test_health.py        # Example: Health endpoint test
└── test_*.py             # Add your test files here
```

## Writing Tests

### Example Test Structure

See `test_health.py` for a simple example of testing an API endpoint:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
```

### Testing Patterns

**1. API Endpoint Tests**
```python
def test_example_endpoint():
    response = client.get("/api/example")
    assert response.status_code == 200
    assert response.json() == {"expected": "data"}
```

**2. Service/Business Logic Tests**
```python
from services.example_service import process_data

def test_process_data():
    result = process_data({"input": "test"})
    assert result["output"] == "expected"
```

**3. Database Tests (if using)**
```python
import pytest

@pytest.fixture
def db():
    # Setup test database
    yield db_connection
    # Teardown

def test_database_operation(db):
    # Test database operations
    pass
```

**4. Validation Tests**
```python
from models.schemas import ExampleModel
from pydantic import ValidationError

def test_model_validation():
    # Valid data
    valid = ExampleModel(name="test", value=123)
    assert valid.name == "test"

    # Invalid data
    with pytest.raises(ValidationError):
        ExampleModel(name="test", value="not_a_number")
```

## Running Tests

```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_health.py -v

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run with verbose output
uv run pytest -v --tb=short
```

## Fixtures

Add shared fixtures to `conftest.py`:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_data():
    return {"key": "value"}
```

Then use in tests:
```python
def test_with_fixture(client, sample_data):
    response = client.post("/api/endpoint", json=sample_data)
    assert response.status_code == 200
```

## Best Practices

1. **One Test, One Assertion (when possible)**
   - Test one specific behavior per test function
   - Makes failures easier to diagnose

2. **Descriptive Test Names**
   - Use `test_function_name_expected_behavior` pattern
   - Example: `test_create_user_returns_201_on_success`

3. **Arrange-Act-Assert Pattern**
   ```python
   def test_example():
       # Arrange: Setup test data
       data = {"key": "value"}

       # Act: Perform the action
       result = function_under_test(data)

       # Assert: Verify the result
       assert result == expected_value
   ```

4. **Test Edge Cases**
   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error conditions

5. **Mock External Dependencies**
   ```python
   from unittest.mock import patch

   @patch('services.external_api.call')
   def test_with_mock(mock_call):
       mock_call.return_value = {"mocked": "response"}
       result = my_function()
       assert result["mocked"] == "response"
   ```

## Test Organization

Organize tests to mirror your application structure:

```
tests/
├── api/
│   └── test_routes.py       # API route tests
├── services/
│   └── test_services.py     # Business logic tests
├── models/
│   └── test_schemas.py      # Pydantic model tests
└── test_health.py           # Health check test
```

## Continuous Integration

Tests are automatically run by:
- ADW `/test` command
- Pre-commit hooks (if configured)
- CI/CD pipelines

Ensure all tests pass before:
- Committing code
- Creating pull requests
- Deploying to production

## Coverage

Aim for:
- **80%+ code coverage** for production code
- **100% coverage** for critical business logic
- **Test all API endpoints**
- **Test error conditions**

Check coverage:
```bash
uv run pytest --cov=. --cov-report=term-missing
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Testing](https://docs.pydantic.dev/latest/concepts/testing/)
