# Augment Existing Test File

Add missing test scenarios to existing file without breaking existing tests.

## Variables
context_json: $1 - Context including existing code and missing scenarios

## Context Structure
```json
{
  "test_file_path": "app/server/tests/test_auth.py",
  "existing_test_code": "/* current test code */",
  "source_code": "/* source being tested */",
  "missing_scenarios": [
    "Test validation fails with expired token",
    "Test user registration"
  ],
  "edge_cases": ["Empty email", "Expired tokens"],
  "issues_to_fix": ["test_register_user has no assertions"]
}
```

## Instructions

1. Read and understand existing test code
2. Identify testing pattern/style used
3. For each missing scenario:
   - Write new test function
   - Follow existing pattern
   - Use appropriate assertions
   - Cover edge cases

4. Fix any issues:
   - Add assertions to stubs
   - Fix incorrect tests

5. Use Edit tool to add to file:
   - Add after existing tests
   - Maintain consistent style
   - Don't break existing tests

## Example

Existing:
```python
def test_magic_link_generation():
    assert True  # stub
```

Missing: ["Test validation with expired token"]
Issues: ["test_magic_link_generation has no assertions"]

Add:
```python
def test_magic_link_generation():
    # Fixed stub
    result = generate_magic_link("test@example.com")
    assert result.token is not None

def test_validate_expired_token():
    """Test validation fails with expired token"""
    response = client.post("/api/auth/validate", json={"token": "expired"})
    assert response.status_code == 401
```

## Output
Return test file path:
```
/absolute/path/to/test_file.py
```
