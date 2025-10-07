# Fix Plan: Add [ADW-BOT] Identifier to All Issue Comments

**Issue:** ADW workflow comments containing state JSON with `"adw_id"` are triggering webhook classification loops because they lack the `[ADW-BOT]` identifier.

**Impact:**
- Creates unnecessary temp classification folders (`agents/4ee44d0c/`, `agents/3dcb452a/`, etc.)
- Wastes API calls to `/classify_adw` command
- Clutters the `agents/` directory

**Root Cause:** 27 locations are posting comments with direct f-string formatting instead of using `format_issue_message()` which adds the bot identifier.

---

## Part 1: Code Refactoring Decision

### Should `format_issue_message()` Move to `utils.py`?

**Current Location:** `adws/adw_modules/workflow_ops.py:45-52`

**Analysis:**

✅ **Arguments FOR moving to `utils.py`:**
1. **Cross-cutting utility** - Used by 27+ locations across 14 files
2. **Better separation of concerns** - String formatting is a utility function, not a workflow operation
3. **More discoverable** - Developers naturally look in `utils.py` for helper functions
4. **Reduces coupling** - `workflow_ops.py` should focus on workflow logic, not string utilities
5. **Consistent with other utilities** - `make_adw_id()`, `setup_logger()`, `parse_json()` are all in `utils.py`

❌ **Arguments AGAINST moving:**
1. **Minimal dependency** - Only depends on `ADW_BOT_IDENTIFIER` constant from `github.py`
2. **Import changes required** - All files currently import from `workflow_ops` would need updating

### **Recommendation: MOVE to `utils.py`**

The function is a formatting utility used system-wide. The single dependency (`ADW_BOT_IDENTIFIER`) is just a constant string and worth the small coupling.

---

## Part 2: Implementation Plan

### Step 1: Move `format_issue_message()` to `utils.py`

**File:** `adws/adw_modules/utils.py`

**Add after line 243 (end of file):**

```python
def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier.

    This function adds the [ADW-BOT] identifier to prevent webhook loops when
    ADW posts comments to GitHub issues. Without this identifier, comments
    containing "adw_" (like state JSON) would trigger classification webhooks.

    Args:
        adw_id: The ADW workflow ID (8-character UUID)
        agent_name: The agent posting the comment (e.g., "ops", "planner", "implementor")
        message: The message content to post
        session_id: Optional session identifier for multi-session agents

    Returns:
        Formatted message with [ADW-BOT] identifier

    Examples:
        >>> format_issue_message("3e81e604", "ops", "Starting review")
        '[ADW-BOT] 3e81e604_ops: Starting review'

        >>> format_issue_message("3e81e604", "planner", "Plan created", "session_1")
        '[ADW-BOT] 3e81e604_planner_session_1: Plan created'
    """
    # Import here to avoid circular dependency
    from adw_modules.github import ADW_BOT_IDENTIFIER

    if session_id:
        return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"
```

**Add import at top of file (after line 10):**

```python
from typing import Any, TypeVar, Type, Union, Dict, Optional  # Optional already exists
```

### Step 2: Remove from `workflow_ops.py`

**File:** `adws/adw_modules/workflow_ops.py`

**Delete lines 45-52:**

```python
def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier."""
    # Always include ADW_BOT_IDENTIFIER to prevent webhook loops
    if session_id:
        return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"
```

**Update imports (line 18):**

```python
# BEFORE:
from adw_modules.github import get_repo_url, extract_repo_path, ADW_BOT_IDENTIFIER

# AFTER:
from adw_modules.github import get_repo_url, extract_repo_path
from adw_modules.utils import format_issue_message
```

### Step 3: Update All Import Statements

**Files that currently import `format_issue_message` from `workflow_ops`:**

Search for: `from adw_modules.workflow_ops import.*format_issue_message`

**Update each to:**

```python
# BEFORE:
from adw_modules.workflow_ops import (
    ...,
    format_issue_message,
    ...
)

# AFTER:
from adw_modules.workflow_ops import (
    ...,
    # format_issue_message moved to utils
    ...
)
from adw_modules.utils import format_issue_message
```

---

## Part 3: Fix All 27 Direct f-string Usages

### Pattern to Replace

**WRONG (all 27 instances):**
```python
make_issue_comment(
    issue_number,
    f"{adw_id}_ops: 🔍 Message...\n```json\n{json.dumps(state.data, indent=2)}\n```"
)
```

**CORRECT:**
```python
make_issue_comment(
    issue_number,
    format_issue_message(adw_id, "ops", f"🔍 Message...\n```json\n{json.dumps(state.data, indent=2)}\n```")
)
```

**Key Changes:**
1. Wrap entire message with `format_issue_message(adw_id, "ops", ...)`
2. Remove `{adw_id}_ops:` from the message (function adds it)
3. Keep the emoji and rest of message content

---

## Part 4: All 27 Locations to Fix

### Files Requiring `format_issue_message` Import

**Add to imports in these files:**
```python
from adw_modules.utils import format_issue_message
```

| File | Count | Lines to Fix |
|------|-------|--------------|
| `adw_build_iso.py` | 2 | 79, 283 |
| `adw_build.py` | 1 | 75 |
| `adw_document_iso.py` | 2 | 320, 528 |
| `adw_document.py` | 1 | 214 |
| `adw_patch_iso.py` | 2 | 322, 441 |
| `adw_patch.py` | 2 | 187, 333 |
| `adw_plan_iso.py` | 2 | 149, 347 |
| `adw_plan.py` | 2 | 110, 297 |
| `adw_review_iso.py` | 2 | 352, 544 |
| `adw_review.py` | 1 | 426 |
| `adw_sdlc_zte_iso.py` | 5 | 82, 147, 174, 214, 232 |
| `adw_ship_iso.py` | 1 | 324 |
| `adw_test_iso.py` | 2 | 686, 876 |
| `adw_modules/git_ops.py` | 2 | 174, 199 |

### Detailed Fix Examples

#### Example 1: State JSON Comment

**File:** `adws/adw_review.py:426`

**BEFORE:**
```python
make_issue_comment(
    issue_number,
    f"{adw_id}_ops: 🔍 Found existing state - starting review\n```json\n{json.dumps(state.data, indent=2)}\n```",
)
```

**AFTER:**
```python
make_issue_comment(
    issue_number,
    format_issue_message(adw_id, "ops", f"🔍 Found existing state - starting review\n```json\n{json.dumps(state.data, indent=2)}\n```"),
)
```

#### Example 2: Simple Status Message

**File:** `adws/adw_modules/git_ops.py:174`

**BEFORE:**
```python
make_issue_comment(issue_number, f"{adw_id}_ops: ✅ Pull request: {pr_url}")
```

**AFTER:**
```python
make_issue_comment(issue_number, format_issue_message(adw_id, "ops", f"✅ Pull request: {pr_url}"))
```

#### Example 3: ZTE Status Update

**File:** `adws/adw_sdlc_zte_iso.py:82`

**BEFORE:**
```python
f"{adw_id}_ops: 🚀 **Starting Zero Touch Execution (ZTE)**\n\n"
```

**AFTER:**
```python
format_issue_message(adw_id, "ops", f"🚀 **Starting Zero Touch Execution (ZTE)**\n\n")
```

---

## Part 5: Testing Plan

### 1. Unit Test

Create `adws/adw_tests/test_format_message.py`:

```python
#!/usr/bin/env python3
"""Test format_issue_message function."""

from adw_modules.utils import format_issue_message

def test_basic_message():
    """Test basic message formatting."""
    result = format_issue_message("3e81e604", "ops", "Test message")
    assert result == "[ADW-BOT] 3e81e604_ops: Test message"
    print("✓ Basic message test passed")

def test_message_with_session():
    """Test message with session ID."""
    result = format_issue_message("3e81e604", "planner", "Test", "session_1")
    assert result == "[ADW-BOT] 3e81e604_planner_session_1: Test"
    print("✓ Session ID test passed")

def test_message_with_json():
    """Test message containing state JSON."""
    import json
    state = {"adw_id": "3e81e604", "issue_number": "7"}
    result = format_issue_message("3e81e604", "ops", f"State:\n```json\n{json.dumps(state)}\n```")
    assert result.startswith("[ADW-BOT]")
    assert "3e81e604_ops:" in result
    assert '"adw_id"' in result
    print("✓ JSON message test passed")

if __name__ == "__main__":
    test_basic_message()
    test_message_with_session()
    test_message_with_json()
    print("\n✅ All tests passed!")
```

**Run:** `uv run adws/adw_tests/test_format_message.py`

### 2. Integration Test

**Test webhook doesn't trigger on bot comments:**

1. Create test issue #999
2. Post comment with bot identifier:
   ```
   [ADW-BOT] 3e81e604_ops: Test state
   ```json
   {"adw_id": "test123"}
   ```
   ```
3. Check webhook logs - should see "Ignoring ADW bot comment to prevent loop"
4. Verify NO new `agents/` folder created

### 3. Verify Existing Workflows

After changes, run a full workflow:

```bash
# Test on a new issue
uv run adws/adw_plan_build_test_review.py 999
```

**Verify:**
- All comments have `[ADW-BOT]` prefix
- No temp classification folders created
- Workflow completes successfully
- Check `agents/` directory - should only see real workflow folders

---

## Part 6: Cleanup Temp Folders (Optional)

### Remove Existing Temp Classification Folders

**Identify temp folders:**
```bash
# Folders with only adw_classifier/ subdirectory are temp
find agents -maxdepth 2 -type d -name "adw_classifier" | while read dir; do
    parent=$(dirname "$dir")
    count=$(find "$parent" -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [ "$count" -eq 1 ]; then
        echo "Temp folder: $parent"
    fi
done
```

**Safe removal:**
```bash
# Review first, then remove
rm -rf agents/3dcb452a agents/826887db agents/93d28b71 agents/f2319321 agents/4ee44d0c
```

---

## Part 7: Implementation Checklist

- [ ] **Step 1:** Move `format_issue_message()` to `utils.py`
- [ ] **Step 2:** Remove function from `workflow_ops.py`
- [ ] **Step 3:** Update `workflow_ops.py` imports
- [ ] **Step 4:** Add import to all 14 affected files
- [ ] **Step 5:** Fix all 27 direct f-string usages
- [ ] **Step 6:** Create and run unit tests
- [ ] **Step 7:** Run integration test on new issue
- [ ] **Step 8:** Verify no temp folders created
- [ ] **Step 9:** Clean up existing temp folders
- [ ] **Step 10:** Update documentation (README.md)

---

## Part 8: Estimated Impact

### Before Fix:
- Every state JSON comment triggers webhook
- Creates temp classification folder
- Wastes 1 API call to `/classify_adw` per comment
- ~5-10 temp folders per workflow run

### After Fix:
- Zero webhook triggers from ADW comments
- Zero temp classification folders
- Zero wasted API calls
- Clean `agents/` directory

### API Cost Savings:
- **Per workflow:** ~10 wasted classifications × $0.001 = $0.01 saved
- **Per 100 workflows:** $1.00 saved
- **Per 1000 workflows:** $10.00 saved

---

## Part 9: Risk Assessment

### Risks:
1. **Import errors** if `format_issue_message` import missing
2. **Circular dependency** if utils imports from workflow_ops (resolved by local import)
3. **Webhook still triggers** if bot identifier format changes

### Mitigations:
1. Test imports in all 14 files
2. Use local import in `format_issue_message()` for `ADW_BOT_IDENTIFIER`
3. Add unit tests to verify identifier format

### Rollback Plan:
If issues occur, revert by:
1. `git revert <commit-hash>`
2. Or manually move function back to `workflow_ops.py`
3. Or use git stash to save changes

---

## Part 10: Future Considerations

### Prevent Future Occurrences:

1. **Add linting rule:**
   ```python
   # .pylintrc or ruff.toml
   # Warn on direct f"{adw_id}_" formatting in make_issue_comment calls
   ```

2. **Add to PR template:**
   ```markdown
   - [ ] All `make_issue_comment()` calls use `format_issue_message()`
   - [ ] No direct f-string formatting with `{adw_id}_`
   ```

3. **Update developer docs:**
   ```markdown
   ## Posting Issue Comments

   ✅ ALWAYS use `format_issue_message()`:
   ```python
   from adw_modules.utils import format_issue_message
   make_issue_comment(issue_num, format_issue_message(adw_id, "ops", "message"))
   ```

   ❌ NEVER use direct f-strings:
   ```python
   make_issue_comment(issue_num, f"{adw_id}_ops: message")  # WRONG!
   ```
   ```

---

## Summary

**Total Changes Required:**
- 1 function moved (`utils.py`)
- 1 function removed (`workflow_ops.py`)
- 14 files need import updates
- 27 specific lines need f-string replacement

**Estimated Time:** 2-3 hours (including testing)

**Benefits:**
- Eliminates webhook classification loops
- Reduces API costs by ~10 calls per workflow
- Cleaner `agents/` directory
- Better code organization (utility in utils.py)

**Next Steps:**
1. Review this document
2. Create feature branch: `git checkout -b fix/adw-bot-identifier`
3. Follow implementation checklist
4. Test thoroughly
5. Commit and create PR
