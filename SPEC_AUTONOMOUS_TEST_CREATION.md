# Autonomous Test Creation System

**Date:** 2025-10-06
**Purpose:** Self-healing test creation and validation system for ADW workflows
**Location:** Integrated into `adws/adw_test.py`

---

## Problem Statement

The ADW system currently has a gap in test validation:
1. Plans specify test files to create (e.g., `test_auth.py`, `test_users.py`)
2. Implementor often ignores test creation requirements
3. Test runner only runs existing tests - doesn't verify new tests were created
4. Reviewer validates UI/spec match - doesn't check test coverage
5. **Result:** Features ship without unit tests

---

## Solution Overview

Add **autonomous test creation and validation** to `adw_test.py` that:
1. ✅ Extracts test requirements from plan (AI)
2. ✅ Validates existing tests match requirements (AI + Python)
3. ✅ Creates missing tests automatically (AI)
4. ✅ Augments incomplete tests (AI)
5. ✅ Validates created tests actually pass (pytest)
6. ✅ Reports all actions to GitHub

**Goal:** Ensure 100% of planned tests exist and pass before continuing to review phase.

---

## System Architecture

### Hybrid AI + Python Design

**Python handles:**
- File existence checks (instant)
- Obvious failure detection (empty files, no test functions)
- Orchestration and control flow
- Git operations
- Reporting to GitHub

**AI handles:**
- Semantic understanding of plan requirements
- Validating tests match requirements
- Generating test code
- Augmenting existing tests
- Fixing failing tests

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  ADW_TEST ENHANCED WORKFLOW                  │
└─────────────────────────────────────────────────────────────┘

START: adw_test.py main()
  ↓
┌─────────────────────────────────────────────────────────────┐
│ NEW: Test Ensurance Phase                                    │
├─────────────────────────────────────────────────────────────┤
│ ensure_tests_exist_and_complete(plan_file, adw_id, ...)     │
│   ↓                                                          │
│   Steps 1-7 (detailed below)                                 │
│   ↓                                                          │
│   Returns: TestEnsuranceReport                               │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ EXISTING: Run Full Test Suite                                │
├─────────────────────────────────────────────────────────────┤
│ run_tests_with_resolution(...)                               │
│ • Runs pytest, type-check, build                             │
│ • Now includes auto-created tests                            │
│ • Resolves any failures                                      │
└─────────────────────────────────────────────────────────────┘
  ↓
CONTINUE: Review, Document, etc.
```

---

## Detailed Steps

### STEP 1: Extract Test Requirements (AI - Single Call)

**Input:** Plan file path
**Agent:** `/extract_test_requirements`
**Output:** JSON array of test requirements

```json
[
  {
    "test_file_path": "app/server/tests/test_auth.py",
    "source_file_path": "app/server/api/routes/auth.py",
    "description": "Tests for authentication endpoints",
    "test_scenarios": [
      "Test magic link generation creates valid token",
      "Test magic link validation succeeds with valid token",
      "Test magic link validation fails with expired token",
      "Test magic link validation fails with used token",
      "Test user registration creates user and experience profile"
    ],
    "relevant_edge_cases": [
      "Empty email in registration/login forms",
      "Invalid email format",
      "Expired magic link tokens",
      "Already used magic link tokens"
    ]
  }
]
```

**Time:** ~5-10 seconds
**Cost:** 1 API call

---

### STEP 2: Fast Python Pre-Filter (Deterministic)

**Purpose:** Eliminate obvious cases to reduce AI validation load

**Python checks for each test:**
```python
1. File exists?
   NO  → Category: "missing" (create from scratch)
   YES → Continue to step 2

2. File is obviously broken?
   - Empty or <10 lines?
   - No test functions (def test_*)?
   - No assertions anywhere?

   YES → Category: "obviously_broken" (replace)
   NO  → Category: "needs_validation" (AI must check)
```

**Output Categories:**
- `missing`: Files that don't exist
- `obviously_broken`: Files that exist but are empty/stubs
- `needs_validation`: Files with content (AI validates correctness)

**Time:** <1 second
**Cost:** $0

---

### STEP 3: AI Deep Validation (Batched)

**Skip if:** `needs_validation` list is empty

**Input:** All files needing validation in one batch
```json
{
  "tests_to_validate": [
    {
      "requirements": { /* from step 1 */ },
      "existing_code": "/* actual file content */",
      "quick_analysis": {
        "has_imports": true,
        "test_count": 3,
        "assertion_count": 2
      }
    }
  ]
}
```

**Agent:** `/validate_test_batch`

**Output:** Validation results for each file
```json
[
  {
    "test_file_path": "app/server/tests/test_auth.py",
    "status": "complete|incomplete|wrong",
    "coverage_analysis": {
      "required_scenarios": 5,
      "implemented_scenarios": 2,
      "missing_scenarios": [
        "Test magic link validation fails with expired token",
        "Test magic link validation fails with used token",
        "Test user registration creates user and experience profile"
      ]
    },
    "issues": [
      "No tests for expired token validation",
      "Missing edge case: empty email handling",
      "test_register_user is a stub with no assertions"
    ],
    "recommendation": "complete|augment|replace"
  }
]
```

**Time:** ~10-15 seconds (batched)
**Cost:** 1 API call

---

### STEP 4: Determine Actions (Python Logic)

**Combine all results:**
```python
actions = {
    "skip": [],      # Files that are complete
    "create": [],    # From "missing" category
    "replace": [],   # From "obviously_broken" + validation "replace"
    "augment": []    # From validation "augment"
}
```

**Report to GitHub:**
```markdown
📊 Test Validation Results:
• 5 test files required by plan
• 2 tests complete and correct ✓
• 1 test missing (will create)
• 2 tests incomplete (will augment)
```

**Time:** <1 second

---

### STEP 5: Execute Actions (Parallel AI Calls)

**For each action type, call appropriate agent in parallel (max 3 concurrent):**

#### CREATE Action
**Agent:** `/create_test`
**Input:** Complete context package
```json
{
  "test_file_path": "app/server/tests/test_auth.py",
  "source_file_path": "app/server/api/routes/auth.py",
  "source_code": "/* actual code from auth.py */",
  "description": "Tests for authentication endpoints",
  "test_scenarios": ["..."],
  "relevant_edge_cases": ["..."],
  "example_test_code": "/* code from test_health.py */",
  "testing_framework": "pytest"
}
```

#### AUGMENT Action
**Agent:** `/augment_test`
**Input:** Existing code + what's missing
```json
{
  "test_file_path": "app/server/tests/test_auth.py",
  "existing_test_code": "/* current code */",
  "source_code": "/* source being tested */",
  "missing_scenarios": ["..."],
  "edge_cases": ["..."],
  "issues_to_fix": ["test_register_user has no assertions"]
}
```

#### REPLACE Action
Same as CREATE (ignore existing file)

**Parallel Execution:**
```python
with ThreadPoolExecutor(max_workers=3) as executor:
    # Submit all tasks
    futures = [...]

    # Collect results as they complete
    for future in as_completed(futures):
        result = future.result()
```

**Track Results:**
```python
{
  "created": ["app/server/tests/test_auth.py"],
  "augmented": ["app/server/tests/test_users.py"],
  "failed": []
}
```

**Time:** ~20-30 seconds (parallel)
**Cost:** N API calls (N = number of actions)

---

### STEP 6: Validate Created Tests (Critical!)

**For each created/augmented test file:**

```python
# Run pytest on ONLY this specific file
result = subprocess.run(
    ["pytest", "app/server/tests/test_auth.py", "-v", "--tb=short"],
    capture_output=True
)

if result.returncode == 0:
    # ✓ Tests pass
    mark_as_successful()
else:
    # ✗ Tests fail - attempt to fix
    fix_attempt = call_fix_test_agent(
        test_file=test_file,
        error_output=result.stderr,
        requirements=requirements
    )

    # Retry pytest after fix
    # Max 2 fix attempts
```

**Agent:** `/fix_test` (if tests fail)
**Input:**
```json
{
  "test_file_path": "app/server/tests/test_auth.py",
  "test_code": "/* current code */",
  "error_output": "/* pytest error */",
  "requirements": { /* original requirements */ }
}
```

**Final Status:**
```python
{
  "created_and_passing": ["test_auth.py"],
  "augmented_and_passing": ["test_users.py"],
  "created_but_failing": []
}
```

**Time:** ~5-10 seconds per test
**Cost:** +1 API call per failing test (for fix attempts)

---

### STEP 7: Commit and Report

**If any tests were created/augmented:**

```bash
git add app/server/tests/test_*.py
git commit -m "test_creator: feature: add/update unit tests

- Created: test_auth.py (5 scenarios)
- Augmented: test_users.py (3 scenarios added)
- All created tests passing

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Report to GitHub:**
```markdown
✅ Test Creation Complete

**Created Tests:**
- `test_auth.py` - 5 scenarios, all passing ✓
  - Test magic link generation
  - Test validation (valid, expired, used tokens)
  - Test user registration

**Augmented Tests:**
- `test_users.py` - Added 3 scenarios ✓
  - Test get user by email
  - Test update last login
  - Test get user experience

**Coverage:**
- Required scenarios: 12
- Implemented scenarios: 12
- Pass rate: 100%
```

**Time:** ~5 seconds

---

## Required Slash Commands

### 1. `/extract_test_requirements`

**File:** `.claude/commands/extract_test_requirements.md`

```markdown
# Extract Test Requirements from Plan

Read the plan file and extract ALL test file requirements with their context.

## Variables
plan_file: $1 - Path to the feature plan

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

Return ONLY valid JSON (no markdown):

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
```

---

### 2. `/validate_test_batch`

**File:** `.claude/commands/validate_test_batch.md`

```markdown
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

Return ONLY valid JSON array:

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
```

---

### 3. `/create_test`

**File:** `.claude/commands/create_test.md`

```markdown
# Create Test File

Create a complete test file from requirements.

## Variables
context_json: $1 - Complete context for test creation

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
Return ONLY the test file path:
```
/absolute/path/to/test_file.py
```
```

---

### 4. `/augment_test`

**File:** `.claude/commands/augment_test.md`

```markdown
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
```

---

### 5. `/fix_test`

**File:** `.claude/commands/fix_test.md`

```markdown
# Fix Failing Test

Fix a test file that's failing pytest validation.

## Variables
context_json: $1 - Test code, error, and requirements

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

4. Use Edit tool to fix the issues
5. Ensure tests still cover required scenarios

## Output
Return test file path:
```
/absolute/path/to/test_file.py
```
```

---

## Python Code Structure

### Main Entry Point

```python
# adws/adw_test.py

def main():
    """Enhanced ADW test with autonomous test creation."""

    # ... existing setup ...

    # NEW: Test Ensurance Phase
    spec_file = state.get("plan_file")
    if spec_file:
        logger.info("=== Test Ensurance Phase ===")

        report = ensure_tests_exist_and_complete(
            plan_file=spec_file,
            adw_id=adw_id,
            issue_number=issue_number,
            logger=logger
        )

        # Report results to GitHub
        if report.created or report.augmented:
            make_issue_comment(
                issue_number,
                format_test_ensurance_report(report, adw_id)
            )

            # Commit the new/updated tests
            commit_test_changes(report)

    # EXISTING: Run full test suite (now includes created tests)
    results, passed, failed, response = run_tests_with_resolution(
        adw_id, issue_number, logger
    )

    # ... rest of existing logic ...
```

### Core Function

```python
def ensure_tests_exist_and_complete(
    plan_file: str,
    adw_id: str,
    issue_number: str,
    logger: logging.Logger
) -> TestEnsuranceReport:
    """
    Ensure all planned tests exist and are complete.
    Returns report of actions taken.
    """

    # STEP 1: Extract requirements (AI - 1 call)
    logger.info("Step 1: Extracting test requirements from plan...")
    requirements = extract_test_requirements_with_ai(plan_file, adw_id, logger)
    logger.info(f"Found {len(requirements)} test files in plan")

    # STEP 2: Fast Python pre-filter
    logger.info("Step 2: Categorizing tests...")
    categorized = categorize_tests_fast(requirements, logger)
    logger.info(
        f"Missing: {len(categorized['missing'])}, "
        f"Broken: {len(categorized['obviously_broken'])}, "
        f"Need validation: {len(categorized['needs_validation'])}"
    )

    # STEP 3: AI validation (batched - 1 call if needed)
    validation_results = []
    if categorized["needs_validation"]:
        logger.info("Step 3: Validating existing tests with AI...")
        validation_results = validate_tests_batch_with_ai(
            categorized["needs_validation"], adw_id, logger
        )

    # STEP 4: Determine actions
    logger.info("Step 4: Determining actions...")
    actions = determine_actions(categorized, validation_results, logger)
    report_test_analysis_to_github(actions, issue_number, adw_id)

    # STEP 5: Execute actions (parallel)
    if actions_needed(actions):
        logger.info("Step 5: Creating/augmenting tests...")
        execution_results = execute_test_actions_parallel(actions, adw_id, logger)
    else:
        logger.info("Step 5: No test creation needed - all tests complete")
        execution_results = {"created": [], "augmented": [], "failed": []}

    # STEP 6: Validate created tests
    if execution_results["created"] or execution_results["augmented"]:
        logger.info("Step 6: Validating created tests...")
        validated = validate_and_fix_created_tests(
            execution_results, adw_id, logger
        )
    else:
        validated = {"created_and_passing": [], "augmented_and_passing": [], "created_but_failing": []}

    # Build report
    report = TestEnsuranceReport(
        total_required=len(requirements),
        already_complete=len(categorized.get("skip", [])) +
                        len([r for r in validation_results if r["status"] == "complete"]),
        created=len(validated["created_and_passing"]),
        augmented=len(validated["augmented_and_passing"]),
        failed=len(validated["created_but_failing"]),
        all_passing=len(validated["created_but_failing"]) == 0
    )

    logger.info(
        f"Test ensurance complete: "
        f"{report.created} created, "
        f"{report.augmented} augmented, "
        f"{report.already_complete} already complete"
    )

    return report
```

### Helper Functions

```python
def categorize_tests_fast(
    requirements: List[Dict],
    logger: logging.Logger
) -> Dict:
    """
    Fast Python categorization.
    Only eliminates obvious cases.
    """
    result = {
        "missing": [],
        "obviously_broken": [],
        "needs_validation": []
    }

    for req in requirements:
        test_file = req["test_file_path"]

        # Check 1: File exists?
        if not os.path.exists(test_file):
            logger.debug(f"  ✗ {test_file} - missing")
            result["missing"].append(req)
            continue

        # Check 2: Obviously broken?
        with open(test_file) as f:
            content = f.read()

        is_broken = (
            len(content.strip()) < 10 or
            not re.search(r'def test_\w+', content) or
            'assert' not in content
        )

        if is_broken:
            logger.debug(f"  ✗ {test_file} - obviously broken")
            req["content"] = content
            result["obviously_broken"].append(req)
        else:
            logger.debug(f"  ? {test_file} - needs validation")
            req["content"] = content
            result["needs_validation"].append(req)

    return result


def execute_test_actions_parallel(
    actions: Dict,
    adw_id: str,
    logger: logging.Logger,
    max_workers: int = 3
) -> Dict:
    """Execute create/augment actions in parallel."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {"created": [], "augmented": [], "failed": []}

    # Collect all tasks
    tasks = []
    for req in actions.get("create", []):
        tasks.append(("create", req))
    for req in actions.get("augment", []):
        tasks.append(("augment", req))
    for req in actions.get("replace", []):
        tasks.append(("create", req))  # Replace = create new

    if not tasks:
        return results

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                create_or_augment_test, action_type, req, adw_id, logger
            ): (action_type, req)
            for action_type, req in tasks
        }

        for future in as_completed(futures):
            action_type, req = futures[future]
            try:
                success, test_file = future.result()
                if success:
                    results[f"{action_type}d"].append(test_file)
                    logger.info(f"  ✓ {action_type}d {test_file}")
                else:
                    results["failed"].append(test_file)
                    logger.error(f"  ✗ Failed to {action_type} {test_file}")
            except Exception as e:
                logger.error(f"  ✗ Exception during {action_type}: {e}")
                results["failed"].append(req["test_file_path"])

    return results


def validate_and_fix_created_tests(
    results: Dict,
    adw_id: str,
    logger: logging.Logger,
    max_fix_attempts: int = 2
) -> Dict:
    """
    Run pytest on created tests.
    If they fail, attempt to fix.
    """
    validated = {
        "created_and_passing": [],
        "augmented_and_passing": [],
        "created_but_failing": []
    }

    all_tests = results.get("created", []) + results.get("augmented", [])

    for test_file in all_tests:
        action_type = "created" if test_file in results.get("created", []) else "augmented"

        logger.info(f"Validating {test_file}...")

        # Run pytest on just this file
        result = subprocess.run(
            ["pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(test_file)
        )

        if result.returncode == 0:
            # Tests pass!
            validated[f"{action_type}_and_passing"].append(test_file)
            logger.info(f"  ✓ All tests passing in {test_file}")
        else:
            # Tests fail - attempt to fix
            logger.warning(f"  ✗ Tests failing in {test_file}, attempting fix...")

            fixed = attempt_test_fix(
                test_file,
                result.stdout + "\n" + result.stderr,
                adw_id,
                logger,
                max_fix_attempts
            )

            if fixed:
                validated[f"{action_type}_and_passing"].append(test_file)
                logger.info(f"  ✓ Fixed and passing: {test_file}")
            else:
                validated["created_but_failing"].append(test_file)
                logger.error(f"  ✗ Could not fix: {test_file}")

    return validated


def attempt_test_fix(
    test_file: str,
    error_output: str,
    adw_id: str,
    logger: logging.Logger,
    max_attempts: int
) -> bool:
    """Attempt to fix failing test with AI."""

    for attempt in range(1, max_attempts + 1):
        logger.info(f"Fix attempt {attempt}/{max_attempts}...")

        # Read current test code
        with open(test_file) as f:
            test_code = f.read()

        # Call fix agent
        context = {
            "test_file_path": test_file,
            "test_code": test_code,
            "error_output": error_output
        }

        request = AgentTemplateRequest(
            agent_name=f"test_fixer_{attempt}",
            slash_command="/fix_test",
            args=[json.dumps(context, indent=2)],
            adw_id=adw_id
        )

        response = execute_template(request)

        if not response.success:
            logger.error(f"Fix attempt {attempt} failed: {response.output}")
            continue

        # Re-run pytest
        result = subprocess.run(
            ["pytest", test_file, "-v"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(test_file)
        )

        if result.returncode == 0:
            logger.info(f"Fix successful on attempt {attempt}")
            return True

        # Update error for next attempt
        error_output = result.stdout + "\n" + result.stderr

    return False
```

### Data Types

```python
# adws/adw_modules/data_types.py

@dataclass
class TestEnsuranceReport:
    """Report of test ensurance actions."""
    total_required: int
    already_complete: int
    created: int
    augmented: int
    failed: int
    all_passing: bool
```

---

## Performance Characteristics

### Expected Timeline

**Scenario: 10 test files required in plan**

Assume:
- 2 files missing
- 1 file broken stub
- 5 files need validation
- 2 files already complete

**Execution:**
1. Extract requirements: 8s (1 AI call)
2. Python categorization: <1s
3. AI validation (5 files): 12s (1 batched AI call)
4. Create 3 tests in parallel: 25s (3 parallel AI calls)
5. Validate with pytest: 15s
6. Commit: 2s

**Total: ~62 seconds, 5 API calls**

### Cost Analysis

**API Calls:**
- Extract: 1 call (~2k tokens in, ~1k out)
- Validate: 1 call (~5k tokens in, ~3k out)
- Create: 3 calls (~4k tokens in, ~2k out each)
- Fix (if needed): 0-3 calls

**Estimated cost: $0.15-0.30 per test creation session**

---

## Success Criteria

### Must Have
✅ Extract all test requirements from plan
✅ Detect missing/incomplete test files
✅ Create missing tests automatically
✅ Validate created tests actually pass
✅ Report all actions to GitHub

### Should Have
✅ Augment incomplete tests (not just replace)
✅ Fix failing tests automatically (2 attempts)
✅ Batch AI operations for efficiency
✅ Parallel test creation

### Nice to Have
⚪ Cache validation results within session
⚪ Smart retry with backoff
⚪ Test quality scoring

---

## Integration Points

### Modified Files

**Primary:**
- `adws/adw_test.py` - Add test ensurance phase

**New Slash Commands:**
- `.claude/commands/extract_test_requirements.md`
- `.claude/commands/validate_test_batch.md`
- `.claude/commands/create_test.md`
- `.claude/commands/augment_test.md`
- `.claude/commands/fix_test.md`

**Data Types:**
- `adws/adw_modules/data_types.py` - Add `TestEnsuranceReport`

### Unchanged Files
- `adws/adw_review.py` - No changes
- `adws/adw_build.py` - No changes
- Existing test runner logic - No changes

---

## Testing the System

### Manual Test
1. Run ADW on an issue with test requirements
2. Verify tests are created
3. Check they pass pytest
4. Review GitHub comments

### Validation
```bash
# After implementation
cd adws
uv run python adw_test.py 7 3e81e604

# Should see:
# - "Extracting test requirements..."
# - "Found X test files in plan"
# - "Creating Y tests..."
# - "✓ All tests passing"
```

---

## Rollback Plan

If issues arise:
1. Comment out test ensurance in `adw_test.py` main()
2. System reverts to existing behavior
3. No breaking changes to other workflows

---

## Future Enhancements

### Phase 2 (Later)
- Test quality scoring (coverage, assertions per test)
- Integration with code coverage tools
- Smart test prioritization
- Frontend test creation (React component tests)

### Phase 3 (Future)
- ML-based test generation
- Property-based testing integration
- Mutation testing validation

---

## Questions & Decisions

### Q: What if plan doesn't specify tests?
**A:** System skips test ensurance phase gracefully.

### Q: What if created tests fail and can't be fixed?
**A:** Report failure to GitHub, continue with existing tests, mark as incomplete.

### Q: Should we validate tests that already exist and pass?
**A:** Only if plan explicitly changed. Use AI to compare plan vs existing tests.

### Q: What about frontend tests?
**A:** Start with backend (Python/pytest). Add frontend (TypeScript/vitest) in Phase 2.

---

## Implementation Checklist

- [ ] Create 5 new slash command files
- [ ] Add `TestEnsuranceReport` data type
- [ ] Implement `ensure_tests_exist_and_complete()` in adw_test.py
- [ ] Implement `categorize_tests_fast()`
- [ ] Implement `execute_test_actions_parallel()`
- [ ] Implement `validate_and_fix_created_tests()`
- [ ] Add GitHub reporting functions
- [ ] Add commit logic for new tests
- [ ] Test on sample ADW workflow
- [ ] Document in CHANGELOG.md

---

**End of Specification**
