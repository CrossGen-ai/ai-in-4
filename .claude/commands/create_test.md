# Create Test File

Create a complete test file from requirements.

## Variables
context_json: $ARGUMENTS - Complete context for test creation

## Context Structure
```json
{
  "test_file_path": "app/server/tests/test_auth.py",
  "source_file_path": "app/server/api/routes/auth.py",
  "source_code": "/* actual source code */",
  "description": "Tests for authentication endpoints",
  "test_scenarios": [
    "Test magic link generation creates valid token",
    "Test magic link validation succeeds with valid token"
  ],
  "relevant_edge_cases": [
    "Empty email",
    "Expired tokens"
  ],
  "example_test_code": "/* pattern from test_health.py */",
  "testing_framework": "pytest"
}
```

## Instructions

### Step 1: Understand Context
- You are creating: `{test_file_path}`
- You are testing: `{source_file_path}`
- Source code provided in `{source_code}`
- Read to understand all functions/endpoints

### Step 2: Follow Pattern
- Framework: `{testing_framework}`
- Example: `{example_test_code}`
- Match this pattern for imports and structure

### Step 3: Write Tests

For EACH scenario in `{test_scenarios}`:
1. Create test function: `test_<scenario_name>()`
2. Follow pattern from example
3. Use real assertions (not stubs)
4. Cover edge cases where relevant

### Step 4: Write File

Use Write tool to create `{test_file_path}`:
- Imports matching example pattern
- One test per scenario
- Clear docstrings
- Real assertions
- NO placeholder tests with `pass` or `assert True`

## Example

Given:
```json
{
  "source_code": "def add(a, b): return a + b",
  "test_scenarios": ["Add positive numbers", "Add negative numbers"],
  "edge_cases": ["Zero"],
  "example_test_code": "def test_health():\n    assert 1 == 1"
}
```

Create:
```python
def test_add_positive_numbers():
    """Test adding two positive numbers"""
    result = add(2, 3)
    assert result == 5

def test_add_negative_numbers():
    """Test adding negative numbers"""
    result = add(-2, -3)
    assert result == -5

def test_add_with_zero():
    """Test edge case: zero"""
    result = add(5, 0)
    assert result == 5
```

## Output
Return ONLY the test file path (no explanation):
```
/absolute/path/to/test_file.py
```
