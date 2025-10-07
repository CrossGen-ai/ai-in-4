# Fix Failing Test

Fix a test file that's failing pytest validation.

## Variables
context_json: $ARGUMENTS - Test code, error, and requirements

## Context Structure
```json
{
  "test_file_path": "app/server/tests/test_auth.py",
  "test_code": "/* current test code */",
  "error_output": "/* pytest error output */",
  "requirements": {
    "test_scenarios": [...],
    "source_file_path": "..."
  }
}
```

## Instructions

1. Analyze error output to understand what's failing
2. Read test code to see what's wrong
3. Common fixes:
   - Import errors → Fix imports
   - Assertion errors → Fix assertions/expected values
   - Fixture errors → Add/fix fixtures
   - API changes → Update test to match current API
   - Name errors → Fix variable/function references

4. Use Edit tool to fix the issues
5. Ensure tests still cover required scenarios
6. Do NOT remove tests - fix them

## Output
Return test file path:
```
/absolute/path/to/test_file.py
```
