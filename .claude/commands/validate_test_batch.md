# Validate Test Completeness (Batch)

Compare existing test files against requirements to determine completeness.

## Variables
batch_json: $1 - JSON array of tests to validate

## Input Structure
```json
{
  "tests_to_validate": [
    {
      "requirements": {
        "test_file_path": "...",
        "test_scenarios": [...],
        "relevant_edge_cases": [...]
      },
      "existing_code": "/* actual file content */",
      "quick_analysis": {
        "has_imports": true,
        "test_count": 3
      }
    }
  ]
}
```

## Instructions

For EACH test in the batch:

1. Analyze requirements vs existing code:
   - Does it test the correct source file/module?
   - Are all required scenarios implemented?
   - Are edge cases covered?
   - Are there stub/placeholder tests?

2. Count coverage:
   - Required scenarios: N
   - Implemented scenarios: M
   - Missing scenarios: [list]

3. Identify issues:
   - Stubs with no assertions
   - Wrong endpoints being tested
   - Missing edge case handling

4. Recommend action:
   - **complete**: All requirements satisfied
   - **augment**: Add missing scenarios to existing file
   - **replace**: Tests are wrong, replace entire file

## Output Format

Return ONLY valid JSON array (no markdown, no code blocks):

```json
[
  {
    "test_file_path": "app/server/tests/test_auth.py",
    "status": "complete|incomplete|wrong",
    "coverage_analysis": {
      "required_scenarios": 5,
      "implemented_scenarios": 2,
      "missing_scenarios": [
        "Test validation fails with expired token"
      ]
    },
    "issues": [
      "test_register_user is a stub"
    ],
    "recommendation": "complete|augment|replace"
  }
]
```

## Status Definitions
- **complete**: All requirements satisfied
- **incomplete**: Missing some scenarios
- **wrong**: Tests wrong things entirely

## Recommendation Definitions
- **complete**: No action needed
- **augment**: Add missing tests
- **replace**: Replace entire file
