# Extract Test Requirements from Plan

Read the plan file and extract ALL test file requirements with their context.

## Variables
plan_file: $ARGUMENTS - Path to the feature plan

## Instructions

1. Read the plan file completely
2. Find ALL mentions of test files (patterns):
   - `app/server/tests/test_*.py`
   - `app/client/src/**/*.test.ts`
   - "Write tests in..."
   - Testing Strategy sections

3. For EACH test file found, extract:
   - **test_file_path**: Exact path to test file
   - **source_file_path**: Source file being tested (infer from context)
   - **description**: What this test file should test
   - **test_scenarios**: Specific test cases mentioned in plan
   - **relevant_edge_cases**: Edge cases that apply to this test

4. Return JSON array of test requirements

## Output Format

Return ONLY valid JSON (no markdown, no code blocks):

```json
[
  {
    "test_file_path": "app/server/tests/test_auth.py",
    "source_file_path": "app/server/api/routes/auth.py",
    "description": "Tests for authentication endpoints",
    "test_scenarios": [
      "Test magic link generation creates valid token",
      "Test magic link validation succeeds with valid token"
    ],
    "relevant_edge_cases": [
      "Empty email in registration/login forms",
      "Expired magic link tokens"
    ]
  }
]
```

## Important
- Include ALL test files mentioned in plan
- Infer source file from context (task descriptions, file lists)
- Extract scenarios from Testing Strategy section
- Include relevant edge cases for each test
- Return valid JSON only (will be parsed immediately)
- If no tests found, return empty array: []
