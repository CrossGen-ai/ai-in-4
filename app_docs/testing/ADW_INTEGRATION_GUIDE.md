# ADW Test Doctor Integration Guide

This guide shows how to integrate the Test Doctor system into ADW test workflows.

## Overview

The Test Doctor system consists of:
- **Knowledge Base**: `app_docs/testing/` - Stack-specific patterns and failure docs
- **Slash Commands**: `/test_doctor`, `/create_test`, `/validate_test`
- **Shared Module**: `adw_modules/test_analysis.py` - Unified failure analysis
- **Pattern Tracker**: `adw_modules/test_doctor.py` - Pattern extraction and KB updates

## Integration Points

### 1. Standard Workflow (adw_test.py)

**Location**: After test failures detected (around line 410-430 in `run_tests_with_resolution`)

**Add import**:
```python
from adw_modules.test_analysis import analyze_and_fix_test_failures, should_rerun_tests
```

**Integration code**:
```python
# After line 408 - when we have failed tests
if failed_count > 0 and attempt < max_attempts:
    # Existing comment and resolution code...

    # NEW: Analyze failures with test_doctor
    logger.info("\n=== Running Test Doctor Analysis ===")
    analysis = await analyze_and_fix_test_failures(
        test_output=test_response.output,
        adw_id=adw_id,
        logger=logger,
        working_dir=None,  # Standard mode - main repo
        auto_fix=True,
    )

    logger.info(f"Test Doctor Analysis Complete:")
    logger.info(f"  - Total failures: {analysis['total_failures']}")
    logger.info(f"  - Known patterns: {analysis['known_patterns']}")
    logger.info(f"  - New patterns: {analysis['new_patterns']}")
    logger.info(f"  - Auto-fixes applied: {analysis['fixes_applied']}")

    # If fixes were applied, continue to re-run tests
    if analysis['fixes_applied'] > 0:
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "test_doctor",
                f"🔬 Applied {analysis['fixes_applied']} auto-fixes from Test Doctor"
            ),
        )
        # Continue to next iteration to re-run tests
        continue

    # Otherwise, proceed with existing resolution logic
    # (rest of existing code...)
```

### 2. ISO Workflow (adw_test_iso.py)

**Location**: After test failures detected (around line 350-370 in `run_tests_with_resolution`)

**Add import** (same as above):
```python
from adw_modules.test_analysis import analyze_and_fix_test_failures, should_rerun_tests
```

**Integration code**:
```python
# After detecting failed tests
if failed_count > 0 and attempt < max_attempts:
    # Get working directory from state
    working_dir = state.get_working_directory()

    # NEW: Analyze failures with test_doctor
    logger.info("\n=== Running Test Doctor Analysis (ISO Mode) ===")
    analysis = await analyze_and_fix_test_failures(
        test_output=test_response.output,
        adw_id=adw_id,
        logger=logger,
        working_dir=working_dir,  # ISO mode - use worktree path
        auto_fix=True,
    )

    logger.info(f"Test Doctor Analysis Complete:")
    logger.info(f"  - Total failures: {analysis['total_failures']}")
    logger.info(f"  - Known patterns: {analysis['known_patterns']}")
    logger.info(f"  - New patterns: {analysis['new_patterns']}")
    logger.info(f"  - Auto-fixes applied: {analysis['fixes_applied']}")
    logger.info(f"  - Worktree: {working_dir}")

    # If fixes were applied, continue to re-run tests
    if analysis['fixes_applied'] > 0:
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "test_doctor",
                f"🔬 Applied {analysis['fixes_applied']} auto-fixes from Test Doctor (ISO)"
            ),
        )
        # Continue to next iteration to re-run tests
        continue

    # Otherwise, proceed with existing resolution logic
    # (rest of existing code...)
```

## How It Works

### Workflow Sequence

```
Test Run → Failures Detected
    ↓
Test Doctor Analysis
    ├─ Load KB patterns from app_docs/testing/
    ├─ Match failures against known patterns
    ├─ Calculate confidence scores
    ├─ Generate fixes for high-confidence matches
    └─ Document new patterns (if unknown)
    ↓
Auto-Fix (if confidence ≥ 90%)
    ├─ Apply fixes to test files
    ├─ Standard mode: Apply to main repo
    └─ ISO mode: Apply to worktree
    ↓
Update Knowledge Base
    ├─ Increment pattern frequency
    ├─ Add occurrence to pattern file
    └─ Update README frequency table
    ↓
Re-run Tests
    └─ If fixes applied, run tests again
```

### Standard vs ISO Mode

| Aspect | Standard Mode | ISO Mode |
|--------|--------------|----------|
| Working Dir | Main repo | Worktree (`.worktrees/<adw-id>/`) |
| Fixes Applied To | Main repo files | Worktree files |
| KB Updates | Shared (main repo) | Shared (main repo) |
| Pattern Tracking | Shared tracker | Shared tracker |

**Key**: Both modes update the same knowledge base, but apply fixes to different locations.

## Testing the Integration

### 1. Test with Known Pattern

```bash
# Introduce a known failure (mock import path error)
# Then run workflow
uv run adws/adw_test.py <issue-number>

# Expected: Test Doctor identifies pattern, applies fix, tests pass
```

### 2. Test with New Pattern

```bash
# Introduce a novel failure
# Then run workflow
uv run adws/adw_test.py <issue-number>

# Expected:
# - Test Doctor identifies as new (confidence < 50%)
# - Creates new pattern file in app_docs/testing/failure_patterns/
# - Updates frequency tracker
```

### 3. Test ISO Mode

```bash
# Run in isolated worktree
uv run adws/adw_test_iso.py <issue-number>

# Expected:
# - Fixes applied to worktree files
# - KB updated in main repo
# - Pattern tracker incremented
```

## Configuration

### Enable/Disable Auto-Fix

To disable auto-fix and only get diagnosis:

```python
analysis = await analyze_and_fix_test_failures(
    test_output=test_response.output,
    adw_id=adw_id,
    logger=logger,
    working_dir=working_dir,
    auto_fix=False,  # Only diagnose, don't fix
)
```

### Confidence Threshold

Currently set to "high" (90%+) for auto-fix. To adjust:

Edit `adw_modules/test_analysis.py`:
```python
# Line ~65
if failure.get("confidence") in ["high", "medium"]:  # Allow medium too
    apply_fix(failure["fix"], working_dir=working_dir)
```

## Monitoring

### Check Pattern Frequency

```bash
cat app_docs/testing/pattern_frequency.json | jq .
```

### View KB Metrics

```bash
cat app_docs/testing/README.md | grep "Pattern Frequency Tracker" -A 10
```

### Review Diagnosis Logs

```bash
cat agents/<adw-id>/test_runner/execution.log | grep "Test Doctor"
```

## Troubleshooting

### Test Doctor Not Finding Patterns

**Issue**: Failures not matched against KB
**Solution**:
1. Check KB files exist in `app_docs/testing/failure_patterns/`
2. Verify pattern signatures match actual errors
3. Review diagnosis output for matching logic

### Auto-Fix Not Applied

**Issue**: Fixes suggested but not applied
**Solution**:
1. Check confidence score (must be "high" for auto-fix)
2. Verify file paths in fix are correct
3. Check permissions on target files

### Knowledge Base Not Updating

**Issue**: New patterns not documented
**Solution**:
1. Verify `app_docs/testing/failure_patterns/` is writable
2. Check `pattern_frequency.json` file permissions
3. Review logs for KB update errors

## Next Steps

After integration:

1. **Monitor First Few Runs**: Watch how Test Doctor handles real failures
2. **Refine Patterns**: Update pattern files based on false positives/negatives
3. **Add More Patterns**: Document additional failure types as discovered
4. **Tune Confidence**: Adjust thresholds based on auto-fix success rate

## Future Enhancements

- **ML-based pattern matching**: Use embeddings for semantic similarity
- **Auto-generate test fixes**: Use Claude to generate fixes, not just identify
- **CI/CD integration**: Run Test Doctor on all test failures in CI
- **Dashboard**: Web UI showing pattern trends and KB health
