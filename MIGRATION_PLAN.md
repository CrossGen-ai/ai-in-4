# Hybrid Migration Plan: tac-7 → ai-in-4

**Strategy:** Hybrid Approach (Bulk Copy + Manual Merge)
**Start Date:** 2025-10-05
**Estimated Completion:** 6.5 hours total
**Status:** 🚀 Ready to Execute

---

## Quick Reference

**Progress Overview:**
- [x] Phase 1: Bulk Copy Safe Files (30 min) - IMMEDIATE VALUE ✅ COMPLETE
- [ ] Phase 2: Manual Merge Core Modules (6 hours) - FOUNDATION
- [ ] Phase 3: Configuration Updates (30 min) - FINISHING TOUCHES
- [ ] Phase 4: End-to-End Testing (1 hour) - VALIDATION

**Current Phase:** Phase 2 - Manual Merge Core Modules
**Next Action:** Start with state.py merge (60 min)

---

## Phase 1: Bulk Copy Safe Files ⚡

**Goal:** Get 80% of value in 30 minutes with near-zero risk
**Risk Level:** 🟢 VERY LOW
**Time Estimate:** 30 minutes
**Value:** HIGH (Meta-commands, KPI tracking, Worktree ops, ISO workflows)

### 1.1 Pre-Flight Checks (5 min)

**Current Working Directory:**
```bash
cd ~/Projects/ai-in-4
pwd  # Should show: /Users/crossgenai/Projects/ai-in-4
```

- [x] Verify in correct directory
- [x] Verify tac-7 exists at `~/Teaching/tac-7`
- [x] Check git status is clean

**Validation Commands:**
```bash
# Should show clean working tree
git status

# Should show tac-7 exists
ls ~/Teaching/tac-7/.claude/commands/meta-command.md

# Should show ai-in-4 structure
ls -la .claude/commands/
```

**Success Criteria:**
- ✅ In ai-in-4 directory
- ✅ No uncommitted changes
- ✅ tac-7 accessible

---

### 1.2 Bulk Copy New Commands (10 min)

**Commands to Copy:**
```bash
# Navigate to project root
cd ~/Projects/ai-in-4

# Copy meta-command (CRITICAL - enables self-extension)
cp ~/Teaching/tac-7/.claude/commands/meta-command.md \
   .claude/commands/

# Copy KPI tracking (enables self-awareness)
cp ~/Teaching/tac-7/.claude/commands/track_agentic_kpis.md \
   .claude/commands/

# Copy worktree management
cp ~/Teaching/tac-7/.claude/commands/install_worktree.md \
   .claude/commands/

cp ~/Teaching/tac-7/.claude/commands/cleanup_worktrees.md \
   .claude/commands/

# Copy operational tools
cp ~/Teaching/tac-7/.claude/commands/health_check.md \
   .claude/commands/

cp ~/Teaching/tac-7/.claude/commands/in_loop_review.md \
   .claude/commands/
```

**Checklist:**
- [x] Copied `meta-command.md`
- [x] Copied `track_agentic_kpis.md`
- [x] Copied `install_worktree.md`
- [x] Copied `cleanup_worktrees.md`
- [x] Copied `health_check.md`
- [x] Copied `in_loop_review.md`

**Verify Copy:**
```bash
# Should show 6 new files
ls -l .claude/commands/ | grep -E "(meta-command|track_agentic_kpis|install_worktree|cleanup_worktrees|health_check|in_loop_review)"
```

**Expected Output:**
```
-rw-r--r--  cleanup_worktrees.md
-rw-r--r--  health_check.md
-rw-r--r--  in_loop_review.md
-rw-r--r--  install_worktree.md
-rw-r--r--  meta-command.md
-rw-r--r--  track_agentic_kpis.md
```

---

### 1.3 Bulk Copy New Module (2 min)

**Command:**
```bash
# Copy worktree operations module
cp ~/Teaching/tac-7/adws/adw_modules/worktree_ops.py \
   adws/adw_modules/
```

**Checklist:**
- [x] Copied `worktree_ops.py`

**Verify Copy:**
```bash
# Should show the file exists
ls -lh adws/adw_modules/worktree_ops.py

# Should show ~243 lines
wc -l adws/adw_modules/worktree_ops.py
```

**Expected Output:**
```
243 adws/adw_modules/worktree_ops.py
```

---

### 1.4 Bulk Copy ISO Workflows (5 min)

**Command:**
```bash
# Copy all isolated workflow scripts
cp ~/Teaching/tac-7/adws/adw_*_iso.py adws/
```

**Checklist:**
- [x] Copied all `adw_*_iso.py` files

**Verify Copy:**
```bash
# Should show all iso workflows
ls -1 adws/adw_*_iso.py
```

**Expected Output:**
```
adws/adw_build_iso.py
adws/adw_document_iso.py
adws/adw_patch_iso.py
adws/adw_plan_build_document_iso.py
adws/adw_plan_build_iso.py
adws/adw_plan_build_review_iso.py
adws/adw_plan_build_test_iso.py
adws/adw_plan_build_test_review_iso.py
adws/adw_plan_iso.py
adws/adw_review_iso.py
adws/adw_sdlc_iso.py
adws/adw_sdlc_zte_iso.py
adws/adw_ship_iso.py
adws/adw_test_iso.py
```

**Count Check:**
```bash
# Should show 14 iso workflow files
ls adws/adw_*_iso.py | wc -l
```

**Expected:** 14 files

---

### 1.5 Test Meta-Command (5 min)

**Test Command Generation:**
```bash
# Test that meta-command works
# (This will be run via Claude Code CLI)
```

**In Claude Code, test:**
```
/meta-command test-health "Run a quick health check on the system"
```

**Checklist:**
- [x] Meta-command executes without error
- [x] New command file created in `.claude/commands/`
- [x] Generated command is well-formed

**Expected Outcome:**
- New file: `.claude/commands/test-health.md`
- File contains proper command structure
- Command is immediately usable

---

### 1.6 Commit Phase 1 (3 min)

**Git Commands:**
```bash
# Check what was added
git status

# Add all new files
git add .claude/commands/meta-command.md
git add .claude/commands/track_agentic_kpis.md
git add .claude/commands/install_worktree.md
git add .claude/commands/cleanup_worktrees.md
git add .claude/commands/health_check.md
git add .claude/commands/in_loop_review.md
git add adws/adw_modules/worktree_ops.py
git add adws/adw_*_iso.py

# Commit
git commit -m "feat: Add meta-agentic capabilities from tac-7 (Phase 1: Bulk Copy)

- Add meta-command generation for self-extension
- Add KPI tracking for self-awareness
- Add worktree operations module for isolation
- Add 14 isolated workflow scripts
- Add worktree management commands
- Add operational tools (health check, review workflow)

This is Phase 1 of hybrid migration: safe bulk copy of new files.
All existing workflows remain functional."

# Push
git push
```

**Checklist:**
- [x] Git status shows new files
- [x] All files staged
- [x] Commit created with descriptive message
- [x] Pushed to remote

**Verify Commit:**
```bash
# Should show the commit
git log -1 --oneline

# Should show all new files in commit
git show --name-only
```

---

### 1.7 Phase 1 Success Criteria ✅

**Validation Checklist:**
- [x] 6 new commands in `.claude/commands/`
- [x] `worktree_ops.py` in `adws/adw_modules/`
- [x] 14 iso workflow files in `adws/`
- [x] Meta-command tested and working
- [x] All changes committed and pushed
- [x] Old workflows still functional (`adw_plan.py`, `adw_build.py`, etc.)

**Test Old Workflows Still Work:**
```bash
# Should still work (non-iso version)
uv run adws/adw_plan.py --help
```

**Expected:** No errors, shows usage information

**Phase 1 Complete When:**
- ✅ All checkboxes above are checked
- ✅ Commit pushed to remote
- ✅ Meta-command generates new commands
- ✅ Old workflows unaffected

**Estimated Time:** 30 minutes
**Actual Time:** ~25 minutes ✅ COMPLETE

---

## Phase 2: Manual Merge Core Modules 🔧

**Goal:** Merge enhancements from tac-7 into existing ai-in-4 modules
**Risk Level:** 🟡 MEDIUM (requires careful testing)
**Time Estimate:** 6 hours
**Value:** HIGH (Foundation for iso workflows)

**Strategy:** One file at a time, test after each, commit between changes

---

### 2.1 Merge `state.py` (60 min)

**Objective:** Add new state fields and methods for worktree support

**Current Location:**
- ai-in-4: `adws/adw_modules/state.py` (142 lines)
- tac-7: `~/Teaching/tac-7/adws/adw_modules/state.py` (173 lines)

**Changes to Make:**

#### Step 1: Open side-by-side comparison (5 min)
```bash
# View differences
code --diff ~/Teaching/tac-7/adws/adw_modules/state.py \
            adws/adw_modules/state.py
```

**Checklist:**
- [x] Files open in diff view
- [x] Identified new fields
- [x] Identified new methods

---

#### Step 2: Add new fields to `core_fields` (10 min)

**Current (ai-in-4):**
```python
core_fields = {
    "adw_id", "issue_number", "branch_name", "plan_file", "issue_class"
}
```

**Target (tac-7):**
```python
core_fields = {
    "adw_id", "issue_number", "branch_name", "plan_file", "issue_class",
    "worktree_path", "backend_port", "frontend_port", "model_set", "all_adws"
}
```

**Edit Command:**
```bash
# Open in editor
code adws/adw_modules/state.py
```

**Find and Replace:**
- Find: `core_fields = {"adw_id", "issue_number", "branch_name", "plan_file", "issue_class"}`
- Replace with: (see target above)

**Checklist:**
- [x] Added `worktree_path` to core_fields
- [x] Added `backend_port` to core_fields
- [x] Added `frontend_port` to core_fields
- [x] Added `model_set` to core_fields
- [x] Added `all_adws` to core_fields

---

#### Step 3: Add `get_working_directory()` method (15 min)

**Location:** After the `update()` method

**Code to Add:**
```python
def get_working_directory(self) -> str:
    """Get the working directory for this workflow.

    Returns:
        str: The worktree path if set, otherwise current working directory
    """
    if "worktree_path" in self.data and self.data["worktree_path"]:
        return self.data["worktree_path"]
    return os.getcwd()
```

**Checklist:**
- [x] Method added after `update()`
- [x] Proper docstring included
- [x] Returns worktree_path when available
- [x] Falls back to os.getcwd()

---

#### Step 4: Add `append_adw_id()` method (15 min)

**Location:** After `get_working_directory()`

**Code to Add:**
```python
def append_adw_id(self, adw_id: str):
    """Append an ADW ID to the all_adws list if not already present.

    Args:
        adw_id: The ADW ID to append to the tracking list
    """
    all_adws = self.data.get("all_adws", [])
    if adw_id not in all_adws:
        all_adws.append(adw_id)
        self.data["all_adws"] = all_adws
```

**Checklist:**
- [x] Method added after `get_working_directory()`
- [x] Proper docstring included
- [x] Checks for duplicates
- [x] Updates data dictionary

---

#### Step 5: Test state.py changes (15 min)

**Test Script:**
```bash
# Create test script
cat > test_state.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.state import ADWState

# Test 1: Create state with new fields
print("Test 1: Create state with new fields")
state = ADWState.create("test1234")
state.update(
    issue_number=999,
    branch_name="test-branch",
    plan_file="test_plan.md",
    issue_class="/feature",
    worktree_path="/tmp/test-worktree",
    backend_port=9100,
    frontend_port=9200,
    model_set="heavy"
)
print(f"✓ State created: {state.data}")

# Test 2: Get working directory
print("\nTest 2: Get working directory")
working_dir = state.get_working_directory()
print(f"✓ Working directory: {working_dir}")
assert working_dir == "/tmp/test-worktree", "Working directory should be worktree path"

# Test 3: Append ADW IDs
print("\nTest 3: Append ADW IDs")
state.append_adw_id("adw1")
state.append_adw_id("adw2")
state.append_adw_id("adw1")  # Duplicate
print(f"✓ ADW list: {state.data.get('all_adws')}")
assert len(state.data.get('all_adws', [])) == 2, "Should have 2 unique ADW IDs"

print("\n✅ All state.py tests passed!")
EOF

# Run test
python3 test_state.py
```

**Checklist:**
- [x] Test script created
- [x] Test 1 passes (new fields)
- [x] Test 2 passes (working directory)
- [x] Test 3 passes (append ADW IDs)
- [x] All tests pass

**Expected Output:**
```
Test 1: Create state with new fields
✓ State created: {...}

Test 2: Get working directory
✓ Working directory: /tmp/test-worktree

Test 3: Append ADW IDs
✓ ADW list: ['adw1', 'adw2']

✅ All state.py tests passed!
```

**Cleanup:**
```bash
rm test_state.py
```

---

#### Step 6: Commit state.py changes (5 min)

```bash
git add adws/adw_modules/state.py
git commit -m "feat: Merge state.py enhancements from tac-7

- Add new core fields: worktree_path, backend_port, frontend_port, model_set, all_adws
- Add get_working_directory() method for worktree support
- Add append_adw_id() method for workflow tracking
- Tested: All new fields and methods working correctly

Part of Phase 2: Manual merge of core modules."

git push
```

**Checklist:**
- [x] File staged
- [x] Commit created
- [x] Pushed to remote

**state.py Complete When:**
- ✅ All new fields added
- ✅ Both new methods added
- ✅ Tests pass
- ✅ Committed and pushed

**Estimated Time:** 60 minutes
**Actual Time:** ~15 minutes ✅ COMPLETE

---

### 2.2 Merge `data_types.py` (45 min)

**Objective:** Add new types and enums for enhanced functionality

**Current Location:**
- ai-in-4: `adws/adw_modules/data_types.py` (234 lines)
- tac-7: `~/Teaching/tac-7/adws/adw_modules/data_types.py` (286 lines)

**Changes to Make:**

#### Step 1: Add RetryCode enum (10 min)

**Location:** Near top of file, after imports

**Code to Add:**
```python
from enum import Enum

class RetryCode(str, Enum):
    """Error codes for retry logic."""
    CLAUDE_CODE_ERROR = "claude_code_error"
    TIMEOUT_ERROR = "timeout_error"
    EXECUTION_ERROR = "execution_error"
    ERROR_DURING_EXECUTION = "error_during_execution"
    NONE = "none"
```

**Checklist:**
- [ ] Import Enum added
- [ ] RetryCode class added
- [ ] All 5 codes defined

---

#### Step 2: Add ModelSet type (5 min)

**Location:** After RetryCode enum

**Code to Add:**
```python
from typing import Literal

ModelSet = Literal["base", "heavy"]
```

**Checklist:**
- [ ] Import Literal added
- [ ] ModelSet type defined

---

#### Step 3: Update ADWStateData model (15 min)

**Find:** `class ADWStateData(BaseModel):`

**Add fields:**
```python
class ADWStateData(BaseModel):
    adw_id: str
    issue_number: Optional[int] = None
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[str] = None
    # NEW FIELDS:
    worktree_path: Optional[str] = None
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    model_set: Optional[ModelSet] = "base"
    all_adws: Optional[List[str]] = None
```

**Checklist:**
- [ ] Added `worktree_path` field
- [ ] Added `backend_port` field
- [ ] Added `frontend_port` field
- [ ] Added `model_set` field with default "base"
- [ ] Added `all_adws` field

---

#### Step 4: Add ADWExtractionResult model (10 min)

**Location:** After ADWStateData

**Code to Add:**
```python
class ADWExtractionResult(BaseModel):
    """Result of extracting ADW information from text."""
    has_workflow: bool
    workflow_command: Optional[str] = None
    adw_id: Optional[str] = None
    model_set: Optional[ModelSet] = "base"
```

**Checklist:**
- [ ] ADWExtractionResult class added
- [ ] All fields defined
- [ ] Proper docstring

---

#### Step 5: Test data_types.py changes (5 min)

**Test Script:**
```bash
cat > test_data_types.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.data_types import (
    RetryCode, ModelSet, ADWStateData, ADWExtractionResult
)

# Test 1: RetryCode enum
print("Test 1: RetryCode enum")
assert RetryCode.CLAUDE_CODE_ERROR == "claude_code_error"
assert RetryCode.NONE == "none"
print("✓ RetryCode enum works")

# Test 2: ModelSet type
print("\nTest 2: ModelSet type")
model: ModelSet = "base"
assert model in ["base", "heavy"]
print("✓ ModelSet type works")

# Test 3: ADWStateData with new fields
print("\nTest 3: ADWStateData with new fields")
state = ADWStateData(
    adw_id="test1234",
    worktree_path="/tmp/test",
    backend_port=9100,
    frontend_port=9200,
    model_set="heavy",
    all_adws=["adw1", "adw2"]
)
print(f"✓ ADWStateData: {state}")

# Test 4: ADWExtractionResult
print("\nTest 4: ADWExtractionResult")
result = ADWExtractionResult(
    has_workflow=True,
    workflow_command="adw_plan_build_iso",
    adw_id="abc123",
    model_set="heavy"
)
print(f"✓ ADWExtractionResult: {result}")

print("\n✅ All data_types.py tests passed!")
EOF

python3 test_data_types.py
rm test_data_types.py
```

**Checklist:**
- [ ] RetryCode test passes
- [ ] ModelSet test passes
- [ ] ADWStateData test passes
- [ ] ADWExtractionResult test passes

---

#### Step 6: Commit data_types.py changes (5 min)

```bash
git add adws/adw_modules/data_types.py
git commit -m "feat: Merge data_types.py enhancements from tac-7

- Add RetryCode enum for error handling
- Add ModelSet type for model selection
- Add new fields to ADWStateData (worktree, ports, model_set)
- Add ADWExtractionResult model for workflow extraction
- Tested: All new types and models working correctly

Part of Phase 2: Manual merge of core modules."

git push
```

**Checklist:**
- [ ] File staged
- [ ] Commit created
- [ ] Pushed to remote

**data_types.py Complete When:**
- ✅ All new types added
- ✅ ADWStateData updated
- ✅ Tests pass
- ✅ Committed and pushed

**Estimated Time:** 45 minutes
**Actual Time:** __________ minutes

---

### 2.3 Merge `agent.py` (90 min)

**Objective:** Add model selection, retry logic, and working directory support

**Current Location:**
- ai-in-4: `adws/adw_modules/agent.py` (300 lines)
- tac-7: `~/Teaching/tac-7/adws/adw_modules/agent.py` (562 lines)

**Changes to Make:**

#### Step 1: Add SLASH_COMMAND_MODEL_MAP (20 min)

**Location:** Near top of file, after imports

**Code to Add:**
```python
from typing import Final, Dict
from .data_types import SlashCommand, ModelSet

SLASH_COMMAND_MODEL_MAP: Final[Dict[SlashCommand, Dict[ModelSet, str]]] = {
    "/classify_issue": {"base": "sonnet", "heavy": "sonnet"},
    "/classify_adw": {"base": "sonnet", "heavy": "sonnet"},
    "/generate_branch_name": {"base": "sonnet", "heavy": "sonnet"},
    "/implement": {"base": "sonnet", "heavy": "opus"},
    "/test": {"base": "sonnet", "heavy": "sonnet"},
    "/resolve_failed_test": {"base": "sonnet", "heavy": "opus"},
    "/test_e2e": {"base": "sonnet", "heavy": "sonnet"},
    "/resolve_failed_e2e_test": {"base": "sonnet", "heavy": "opus"},
    "/review": {"base": "sonnet", "heavy": "sonnet"},
    "/document": {"base": "sonnet", "heavy": "opus"},
    "/commit": {"base": "sonnet", "heavy": "sonnet"},
    "/pull_request": {"base": "sonnet", "heavy": "sonnet"},
    "/chore": {"base": "sonnet", "heavy": "opus"},
    "/bug": {"base": "sonnet", "heavy": "opus"},
    "/feature": {"base": "sonnet", "heavy": "opus"},
    "/patch": {"base": "sonnet", "heavy": "opus"},
}
```

**Checklist:**
- [ ] Import Final and Dict added
- [ ] Import SlashCommand and ModelSet added
- [ ] SLASH_COMMAND_MODEL_MAP defined
- [ ] All 16 commands mapped

---

#### Step 2: Add get_model_for_slash_command() function (25 min)

**Location:** After SLASH_COMMAND_MODEL_MAP

**Code to Add:**
```python
def get_model_for_slash_command(
    request: AgentTemplateRequest,
    default: str = "sonnet"
) -> str:
    """Get the appropriate model for a template request based on ADW state
    and slash command.

    This function loads the ADW state to determine the model set (base or heavy)
    and returns the appropriate model for the slash command.

    Args:
        request: The agent template request
        default: Default model if no mapping found

    Returns:
        str: The model to use ("sonnet" or "opus")
    """
    from .state import ADWState

    # Load state to get model_set
    model_set: ModelSet = "base"  # Default model set
    if request.adw_id:
        state = ADWState.load(request.adw_id)
        if state:
            model_set = state.get("model_set", "base")

    # Get the model configuration for the command
    command_config = SLASH_COMMAND_MODEL_MAP.get(request.slash_command)
    if not command_config:
        return default

    return command_config.get(model_set, default)
```

**Checklist:**
- [ ] Function signature correct
- [ ] Proper docstring
- [ ] Loads state to get model_set
- [ ] Returns correct model based on mapping

---

#### Step 3: Add retry logic function (25 min)

**Location:** Before execute_template() function

**Code to Add:**
```python
def prompt_claude_code_with_retry(
    request: AgentTemplateRequest,
    logger: logging.Logger,
    max_retries: int = 3,
    retry_delays: List[int] = [1, 3, 5]
) -> AgentResponse:
    """Execute Claude Code with retry logic.

    Args:
        request: The agent template request
        logger: Logger instance
        max_retries: Maximum number of retry attempts
        retry_delays: Delay in seconds between retries

    Returns:
        AgentResponse with success status and output
    """
    import time
    from .data_types import RetryCode

    for attempt in range(max_retries):
        try:
            response = execute_template(request, logger)

            if response.success:
                return response

            # Check if should retry
            retry_code = response.retry_code
            if retry_code == RetryCode.NONE:
                # Don't retry on NONE
                return response

            # Wait before retry
            if attempt < max_retries - 1:
                delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay")
                time.sleep(delay)

        except Exception as e:
            logger.error(f"Exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                time.sleep(delay)
            else:
                return AgentResponse(
                    success=False,
                    output=str(e),
                    retry_code=RetryCode.EXECUTION_ERROR
                )

    return AgentResponse(
        success=False,
        output="Max retries exceeded",
        retry_code=RetryCode.TIMEOUT_ERROR
    )
```

**Checklist:**
- [ ] Function signature correct
- [ ] Proper docstring
- [ ] Retry loop implemented
- [ ] Exponential backoff
- [ ] Returns proper response

---

#### Step 4: Add working_dir support to execute_template() (15 min)

**Find:** The `execute_template()` function

**Modify to accept and use working_dir:**
```python
def execute_template(
    request: AgentTemplateRequest,
    logger: logging.Logger
) -> AgentResponse:
    """Execute a Claude Code template with optional working directory."""

    # Get working directory from state if available
    from .state import ADWState
    working_dir = None
    if request.adw_id:
        state = ADWState.load(request.adw_id)
        if state:
            working_dir = state.get_working_directory()

    # ... existing code ...

    # When running subprocess, add cwd parameter:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=working_dir  # ADD THIS
    )

    # ... rest of function ...
```

**Checklist:**
- [ ] Import ADWState added
- [ ] working_dir extracted from state
- [ ] subprocess.run() uses cwd parameter

---

#### Step 5: Test agent.py changes (10 min)

**Test Script:**
```bash
cat > test_agent.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.agent import (
    SLASH_COMMAND_MODEL_MAP,
    get_model_for_slash_command
)
from adws.adw_modules.data_types import AgentTemplateRequest

# Test 1: Model map exists
print("Test 1: Model map exists")
assert "/implement" in SLASH_COMMAND_MODEL_MAP
assert SLASH_COMMAND_MODEL_MAP["/implement"]["base"] == "sonnet"
assert SLASH_COMMAND_MODEL_MAP["/implement"]["heavy"] == "opus"
print("✓ Model map correct")

# Test 2: Model selection (no state)
print("\nTest 2: Model selection without state")
request = AgentTemplateRequest(
    slash_command="/implement",
    args=["test"],
    adw_id=None  # No state
)
model = get_model_for_slash_command(request)
assert model == "sonnet"  # Should default to base
print(f"✓ Model selection: {model}")

print("\n✅ All agent.py tests passed!")
EOF

python3 test_agent.py
rm test_agent.py
```

**Checklist:**
- [ ] Model map test passes
- [ ] Model selection test passes

---

#### Step 6: Commit agent.py changes (5 min)

```bash
git add adws/adw_modules/agent.py
git commit -m "feat: Merge agent.py enhancements from tac-7

- Add SLASH_COMMAND_MODEL_MAP for dynamic model selection
- Add get_model_for_slash_command() function
- Add prompt_claude_code_with_retry() for error handling
- Add working_dir support to execute_template()
- Tested: Model selection and basic functionality working

Part of Phase 2: Manual merge of core modules."

git push
```

**Checklist:**
- [ ] File staged
- [ ] Commit created
- [ ] Pushed to remote

**agent.py Complete When:**
- ✅ Model map added
- ✅ Model selection function added
- ✅ Retry logic added
- ✅ Working dir support added
- ✅ Tests pass
- ✅ Committed and pushed

**Estimated Time:** 90 minutes
**Actual Time:** __________ minutes

---

### 2.4 Merge `git_ops.py` (45 min)

**Objective:** Add cwd parameter support to all git operations

**Current Location:**
- ai-in-4: `adws/adw_modules/git_ops.py`
- tac-7: `~/Teaching/tac-7/adws/adw_modules/git_ops.py`

**Changes to Make:**

#### Step 1: Identify all git functions (5 min)

**List functions to update:**
```bash
# Find all function definitions
grep "^def " adws/adw_modules/git_ops.py
```

**Expected functions:**
- `create_branch()`
- `commit_changes()`
- `push_branch()`
- `get_current_branch()`
- Others...

**Checklist:**
- [ ] Listed all functions
- [ ] Identified which need cwd parameter

---

#### Step 2: Add cwd parameter to each function (30 min)

**Pattern for each function:**

**Before:**
```python
def create_branch(branch_name: str):
    """Create a new git branch."""
    cmd = ["git", "checkout", "-b", branch_name]
    subprocess.run(cmd, check=True)
```

**After:**
```python
def create_branch(branch_name: str, cwd: Optional[str] = None):
    """Create a new git branch.

    Args:
        branch_name: Name of the branch to create
        cwd: Working directory for git command
    """
    cmd = ["git", "checkout", "-b", branch_name]
    subprocess.run(cmd, check=True, cwd=cwd)
```

**Apply to all functions:**
- [ ] `create_branch()` - Added cwd parameter
- [ ] `commit_changes()` - Added cwd parameter
- [ ] `push_branch()` - Added cwd parameter
- [ ] `get_current_branch()` - Added cwd parameter
- [ ] Other functions as needed

---

#### Step 3: Test git_ops.py changes (5 min)

**Test Script:**
```bash
cat > test_git_ops.py << 'EOF'
#!/usr/bin/env python3
import tempfile
import os
from adws.adw_modules.git_ops import get_current_branch

# Test 1: Get current branch (no cwd)
print("Test 1: Get current branch in main repo")
branch = get_current_branch()
print(f"✓ Current branch: {branch}")

# Test 2: Get current branch with cwd
print("\nTest 2: Get current branch with cwd parameter")
current_dir = os.getcwd()
branch = get_current_branch(cwd=current_dir)
print(f"✓ Current branch (with cwd): {branch}")

print("\n✅ All git_ops.py tests passed!")
EOF

python3 test_git_ops.py
rm test_git_ops.py
```

**Checklist:**
- [ ] Test without cwd passes
- [ ] Test with cwd passes

---

#### Step 4: Commit git_ops.py changes (5 min)

```bash
git add adws/adw_modules/git_ops.py
git commit -m "feat: Merge git_ops.py enhancements from tac-7

- Add cwd parameter to all git operations
- Enable git commands in worktree directories
- Maintain backward compatibility (cwd=None defaults to current dir)
- Tested: Git operations work with and without cwd

Part of Phase 2: Manual merge of core modules."

git push
```

**Checklist:**
- [ ] File staged
- [ ] Commit created
- [ ] Pushed to remote

**git_ops.py Complete When:**
- ✅ All functions have cwd parameter
- ✅ Tests pass
- ✅ Committed and pushed

**Estimated Time:** 45 minutes
**Actual Time:** __________ minutes

---

### 2.5 Merge `workflow_ops.py` (60 min)

**Objective:** Add model_set extraction and ADWExtractionResult support

**Current Location:**
- ai-in-4: `adws/adw_modules/workflow_ops.py`
- tac-7: `~/Teaching/tac-7/adws/adw_modules/workflow_ops.py`

**Changes to Make:**

#### Step 1: Update extract_adw_info() function (30 min)

**Find:** `def extract_adw_info(text: str, temp_adw_id: str)`

**Modify to:**
1. Add model_set extraction to the prompt
2. Return ADWExtractionResult instead of tuple

**Before:**
```python
def extract_adw_info(text: str, temp_adw_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Extract ADW workflow and ID from text."""
    # ... existing code ...
    return (has_workflow, workflow, adw_id)
```

**After:**
```python
def extract_adw_info(text: str, temp_adw_id: str) -> ADWExtractionResult:
    """Extract ADW workflow, ID, and model set from text.

    Args:
        text: Text to extract from (issue body or comment)
        temp_adw_id: Temporary ADW ID for classification

    Returns:
        ADWExtractionResult with workflow, adw_id, and model_set
    """
    from .data_types import ADWExtractionResult

    # Update prompt to extract model_set
    prompt = f"""
    Analyze this text and extract:
    - workflow_command: The ADW workflow command (e.g., "adw_plan_build_iso")
    - adw_id: The ADW ID if specified (8-character hex)
    - model_set: "base" or "heavy" if specified, otherwise "base"

    Text: {text}

    Return JSON with: {{"has_workflow": bool, "workflow_command": str or null, "adw_id": str or null, "model_set": "base" or "heavy"}}
    """

    # ... execute classification ...

    # Parse response
    data = parse_json(response.output, dict)

    return ADWExtractionResult(
        has_workflow=data.get("has_workflow", False),
        workflow_command=data.get("workflow_command"),
        adw_id=data.get("adw_id"),
        model_set=data.get("model_set", "base")
    )
```

**Checklist:**
- [ ] Import ADWExtractionResult added
- [ ] Function signature updated
- [ ] Prompt updated to extract model_set
- [ ] Returns ADWExtractionResult
- [ ] Proper docstring

---

#### Step 2: Update callers of extract_adw_info() (20 min)

**Find all callers:**
```bash
grep -n "extract_adw_info" adws/*.py adws/adw_triggers/*.py
```

**Update each caller:**

**Before:**
```python
has_workflow, workflow, adw_id = extract_adw_info(text, temp_id)
if has_workflow:
    print(f"Found workflow: {workflow}")
```

**After:**
```python
result = extract_adw_info(text, temp_id)
if result.has_workflow:
    print(f"Found workflow: {result.workflow_command}")
    print(f"Model set: {result.model_set}")
```

**Files to update:**
- [ ] `adws/adw_triggers/trigger_webhook.py`
- [ ] `adws/adw_triggers/trigger_cron.py`
- [ ] Any other callers

---

#### Step 3: Test workflow_ops.py changes (5 min)

**Test Script:**
```bash
cat > test_workflow_ops.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.workflow_ops import extract_adw_info

# Test 1: Extract with model_set heavy
print("Test 1: Extract workflow with model_set heavy")
text = "adw_plan_build_iso model_set heavy"
result = extract_adw_info(text, "temp1234")
print(f"✓ Has workflow: {result.has_workflow}")
print(f"✓ Workflow: {result.workflow_command}")
print(f"✓ Model set: {result.model_set}")

# Test 2: Extract without model_set (should default to base)
print("\nTest 2: Extract workflow without model_set")
text = "adw_plan_build_iso"
result = extract_adw_info(text, "temp5678")
print(f"✓ Has workflow: {result.has_workflow}")
print(f"✓ Model set: {result.model_set}")
assert result.model_set == "base", "Should default to base"

print("\n✅ All workflow_ops.py tests passed!")
EOF

python3 test_workflow_ops.py
rm test_workflow_ops.py
```

**Checklist:**
- [ ] Test with model_set heavy passes
- [ ] Test without model_set defaults to base
- [ ] ADWExtractionResult structure correct

---

#### Step 4: Commit workflow_ops.py changes (5 min)

```bash
git add adws/adw_modules/workflow_ops.py
git add adws/adw_triggers/*.py  # If modified
git commit -m "feat: Merge workflow_ops.py enhancements from tac-7

- Update extract_adw_info() to return ADWExtractionResult
- Add model_set extraction from issue text
- Update all callers to use new result structure
- Tested: Extraction works with and without model_set

Part of Phase 2: Manual merge of core modules."

git push
```

**Checklist:**
- [ ] Files staged
- [ ] Commit created
- [ ] Pushed to remote

**workflow_ops.py Complete When:**
- ✅ extract_adw_info() returns ADWExtractionResult
- ✅ model_set extraction added
- ✅ All callers updated
- ✅ Tests pass
- ✅ Committed and pushed

**Estimated Time:** 60 minutes
**Actual Time:** __________ minutes

---

### 2.6 Phase 2 Success Criteria ✅

**Validation Checklist:**
- [ ] `state.py` merged and tested
- [ ] `data_types.py` merged and tested
- [ ] `agent.py` merged and tested
- [ ] `git_ops.py` merged and tested
- [ ] `workflow_ops.py` merged and tested
- [ ] All 5 modules committed separately
- [ ] All tests passing

**Integration Test:**
```bash
# Test that iso workflows can load state and get working directory
cat > test_integration.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.state import ADWState
from adws.adw_modules.agent import get_model_for_slash_command
from adws.adw_modules.data_types import AgentTemplateRequest

# Create state with all new fields
state = ADWState.create("integration")
state.update(
    worktree_path="/tmp/test-worktree",
    backend_port=9105,
    frontend_port=9205,
    model_set="heavy"
)
state.save()

# Test working directory
working_dir = state.get_working_directory()
assert working_dir == "/tmp/test-worktree"
print(f"✓ Working directory: {working_dir}")

# Test model selection
request = AgentTemplateRequest(
    slash_command="/implement",
    args=["test"],
    adw_id="integration"
)
model = get_model_for_slash_command(request)
assert model == "opus"  # Heavy mode should use opus for /implement
print(f"✓ Model selected: {model}")

print("\n✅ Integration test passed!")
EOF

python3 test_integration.py
rm test_integration.py
```

**Checklist:**
- [ ] Integration test passes
- [ ] All modules work together
- [ ] State flows through system

**Phase 2 Complete When:**
- ✅ All 5 core modules merged
- ✅ All individual tests pass
- ✅ Integration test passes
- ✅ All commits pushed

**Estimated Time:** 6 hours
**Actual Time:** __________ hours

---

## Phase 3: Configuration Updates 🔧

**Goal:** Update commands to support dynamic port configuration
**Risk Level:** 🟢 LOW
**Time Estimate:** 30 minutes
**Value:** MEDIUM (Enables worktree port isolation)

---

### 3.1 Update `start.md` Command (15 min)

**Current Location:** `.claude/commands/start.md`

**Changes to Make:**

#### Step 1: View differences (2 min)
```bash
code --diff ~/Teaching/tac-7/.claude/commands/start.md \
            .claude/commands/start.md
```

**Checklist:**
- [ ] Files open in diff view
- [ ] Identified port configuration section

---

#### Step 2: Update Variables section (8 min)

**Find:** `## Variables` section

**Current:**
```markdown
## Variables
PORT: 5173
```

**Replace with:**
```markdown
## Variables
PORT: If `.ports.env` exists, read FRONTEND_PORT from it, otherwise default to 5173
```

---

#### Step 3: Update Instructions section (5 min)

**Find:** `## Instructions` section

**Add at beginning:**
```markdown
## Instructions

1. Check if `.ports.env` exists in current directory:
   - If it exists, source it and use `FRONTEND_PORT` for the PORT variable
   - If not, use default PORT: 5173

2. [Rest of existing instructions...]
```

**Checklist:**
- [ ] Variables section updated
- [ ] Instructions section updated
- [ ] Port detection logic added

---

#### Step 4: Test start command (5 min)

**Create test .ports.env:**
```bash
# Create test file
echo "FRONTEND_PORT=9999" > .ports.env

# Test that start command would use this port
# (Manual verification in Claude Code)
```

**Checklist:**
- [ ] Test file created
- [ ] Start command detects .ports.env
- [ ] Uses custom port when file exists

**Cleanup:**
```bash
rm .ports.env
```

---

### 3.2 Update `test_e2e.md` Command (15 min)

**Current Location:** `.claude/commands/e2e/test_e2e.md` or similar

**Changes to Make:**

#### Step 1: Update application_url variable (10 min)

**Find:** `application_url:` parameter

**Current:**
```markdown
application_url: $4 if provided, otherwise use http://localhost:5173
```

**Replace with:**
```markdown
application_url: $ARGUMENT if provided, otherwise determine from port configuration:
  - If `.ports.env` exists, source it and use http://localhost:${FRONTEND_PORT}
  - Otherwise use default http://localhost:5173
```

**Checklist:**
- [ ] Variable section updated
- [ ] Port detection logic added

---

#### Step 2: Test test_e2e command (5 min)

**Create test .ports.env:**
```bash
echo "FRONTEND_PORT=9999" > .ports.env

# Verify test_e2e would use this URL
# (Manual verification)
```

**Checklist:**
- [ ] Test file created
- [ ] Command detects .ports.env
- [ ] Uses custom URL when file exists

**Cleanup:**
```bash
rm .ports.env
```

---

### 3.3 Commit Configuration Changes (5 min)

```bash
git add .claude/commands/start.md
git add .claude/commands/test_e2e.md  # Or wherever located
git commit -m "feat: Add dynamic port configuration to commands

- Update start.md to read from .ports.env when available
- Update test_e2e.md to use dynamic port from .ports.env
- Enables worktree isolation with unique ports
- Backward compatible: defaults to 5173 when .ports.env absent

Part of Phase 3: Configuration updates."

git push
```

**Checklist:**
- [ ] Files staged
- [ ] Commit created
- [ ] Pushed to remote

---

### 3.4 Phase 3 Success Criteria ✅

**Validation Checklist:**
- [ ] `start.md` updated for dynamic ports
- [ ] `test_e2e.md` updated for dynamic ports
- [ ] Both commands tested with .ports.env
- [ ] Backward compatible (work without .ports.env)
- [ ] Changes committed and pushed

**Test Backward Compatibility:**
```bash
# Without .ports.env (should use defaults)
# Run start command - should use 5173

# With .ports.env (should use custom port)
echo "FRONTEND_PORT=8888" > .ports.env
# Run start command - should use 8888
rm .ports.env
```

**Checklist:**
- [ ] Works with .ports.env
- [ ] Works without .ports.env
- [ ] No errors either way

**Phase 3 Complete When:**
- ✅ Both commands updated
- ✅ Dynamic port detection working
- ✅ Backward compatible
- ✅ Committed and pushed

**Estimated Time:** 30 minutes
**Actual Time:** __________ minutes

---

## Phase 4: End-to-End Testing 🧪

**Goal:** Validate entire migration works end-to-end
**Risk Level:** 🟢 LOW
**Time Estimate:** 1 hour
**Value:** CRITICAL (Ensures nothing broken)

---

### 4.1 Test Old Workflows Still Work (15 min)

**Objective:** Ensure non-iso workflows unaffected by migration

**Test Non-ISO Plan:**
```bash
# Should work exactly as before
uv run adws/adw_plan.py --help
```

**Checklist:**
- [ ] `adw_plan.py` shows help
- [ ] No import errors
- [ ] No breaking changes

**Test Non-ISO Build:**
```bash
uv run adws/adw_build.py --help
```

**Checklist:**
- [ ] `adw_build.py` shows help
- [ ] No import errors

**Test Other Core Workflows:**
```bash
uv run adws/adw_test.py --help
uv run adws/adw_review.py --help
uv run adws/adw_document.py --help
```

**Checklist:**
- [ ] All old workflows show help
- [ ] No errors
- [ ] Backward compatibility maintained

---

### 4.2 Test New ISO Workflows Exist (10 min)

**Objective:** Verify all iso workflows were copied

**Test ISO Plan:**
```bash
uv run adws/adw_plan_iso.py --help
```

**Checklist:**
- [ ] `adw_plan_iso.py` exists
- [ ] Shows help or runs

**Test All ISO Workflows:**
```bash
for file in adws/adw_*_iso.py; do
    echo "Testing: $file"
    uv run "$file" --help 2>&1 | head -3
done
```

**Checklist:**
- [ ] All 14 iso workflows found
- [ ] No missing file errors
- [ ] Basic execution works

---

### 4.3 Test Meta-Command (10 min)

**Objective:** Verify meta-command generates new commands

**Test Command:**
```
/meta-command test-migration "Verify migration was successful"
```

**Expected:**
- New file created: `.claude/commands/test-migration.md`
- File contains proper structure
- Command is well-formed

**Checklist:**
- [ ] Meta-command executes
- [ ] New file created
- [ ] File is valid markdown
- [ ] Command structure correct

**Cleanup:**
```bash
rm .claude/commands/test-migration.md
```

---

### 4.4 Test KPI Tracking (10 min)

**Objective:** Verify KPI tracking command exists and runs

**Test Command:**
```
/track_agentic_kpis
```

**Expected:**
- Command executes
- Creates or updates `app_docs/agentic_kpis.md`
- No errors

**Checklist:**
- [ ] Command executes
- [ ] Dashboard file created/updated
- [ ] No errors

---

### 4.5 Test Model Selection (10 min)

**Objective:** Verify model selection logic works

**Test Script:**
```bash
cat > test_model_selection.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.state import ADWState
from adws.adw_modules.agent import get_model_for_slash_command
from adws.adw_modules.data_types import AgentTemplateRequest

# Test 1: Base model set
print("Test 1: Base model set")
state = ADWState.create("test_base")
state.update(model_set="base")
state.save()

request = AgentTemplateRequest(
    slash_command="/implement",
    args=["test"],
    adw_id="test_base"
)
model = get_model_for_slash_command(request)
assert model == "sonnet", f"Expected sonnet, got {model}"
print(f"✓ Base uses sonnet: {model}")

# Test 2: Heavy model set
print("\nTest 2: Heavy model set")
state = ADWState.create("test_heavy")
state.update(model_set="heavy")
state.save()

request = AgentTemplateRequest(
    slash_command="/implement",
    args=["test"],
    adw_id="test_heavy"
)
model = get_model_for_slash_command(request)
assert model == "opus", f"Expected opus, got {model}"
print(f"✓ Heavy uses opus: {model}")

print("\n✅ Model selection working!")
EOF

python3 test_model_selection.py
rm test_model_selection.py

# Cleanup
rm -rf agents/test_base agents/test_heavy
```

**Checklist:**
- [ ] Base model set uses sonnet
- [ ] Heavy model set uses opus
- [ ] Model selection logic correct

---

### 4.6 Test Worktree Operations Module (15 min)

**Objective:** Verify worktree_ops.py works

**Test Script:**
```bash
cat > test_worktree.py << 'EOF'
#!/usr/bin/env python3
from adws.adw_modules.worktree_ops import get_ports_for_adw

# Test port allocation
print("Test: Port allocation for ADW IDs")
adw_id_1 = "abc12345"
adw_id_2 = "def67890"

backend_1, frontend_1 = get_ports_for_adw(adw_id_1)
backend_2, frontend_2 = get_ports_for_adw(adw_id_2)

print(f"ADW {adw_id_1}: Backend={backend_1}, Frontend={frontend_1}")
print(f"ADW {adw_id_2}: Backend={backend_2}, Frontend={frontend_2}")

# Verify ports in valid range
assert 9100 <= backend_1 <= 9114, f"Backend port out of range: {backend_1}"
assert 9200 <= frontend_1 <= 9214, f"Frontend port out of range: {frontend_1}"
assert 9100 <= backend_2 <= 9114, f"Backend port out of range: {backend_2}"
assert 9200 <= frontend_2 <= 9214, f"Frontend port out of range: {frontend_2}"

# Same ADW ID should get same ports (deterministic)
backend_1b, frontend_1b = get_ports_for_adw(adw_id_1)
assert backend_1 == backend_1b, "Port allocation not deterministic"
assert frontend_1 == frontend_1b, "Port allocation not deterministic"

print("\n✅ Worktree operations working!")
EOF

python3 test_worktree.py
rm test_worktree.py
```

**Checklist:**
- [ ] Port allocation works
- [ ] Ports in valid range (9100-9114, 9200-9214)
- [ ] Allocation is deterministic
- [ ] No errors

---

### 4.7 Phase 4 Success Criteria ✅

**Complete Integration Checklist:**
- [ ] Old workflows (non-iso) work
- [ ] New workflows (iso) exist and run
- [ ] Meta-command generates commands
- [ ] KPI tracking works
- [ ] Model selection works correctly
- [ ] Worktree operations module works
- [ ] No import errors anywhere
- [ ] No breaking changes

**Final Validation:**
```bash
# Run comprehensive check
echo "=== Checking Old Workflows ==="
ls -1 adws/adw_*.py | grep -v "_iso.py" | head -5

echo "=== Checking ISO Workflows ==="
ls -1 adws/adw_*_iso.py | head -5

echo "=== Checking New Commands ==="
ls -1 .claude/commands/ | grep -E "(meta-command|track_agentic_kpis|install_worktree|cleanup_worktrees|health_check|in_loop_review)"

echo "=== Checking Core Modules ==="
python3 -c "
from adws.adw_modules import state, data_types, agent, git_ops, workflow_ops, worktree_ops
print('✓ All modules import successfully')
"

echo "=== Migration Complete ==="
```

**Checklist:**
- [ ] All old workflows listed
- [ ] All iso workflows listed
- [ ] All new commands listed
- [ ] All modules import
- [ ] No errors in output

**Phase 4 Complete When:**
- ✅ All tests pass
- ✅ No breaking changes
- ✅ All new features work
- ✅ Integration validated

**Estimated Time:** 1 hour
**Actual Time:** __________ minutes

---

## Migration Complete! 🎉

### Final Checklist

**Phase 1: Bulk Copy** ✅
- [ ] 6 new commands copied
- [ ] 1 new module copied
- [ ] 14 iso workflows copied
- [ ] Meta-command tested
- [ ] Committed and pushed

**Phase 2: Manual Merge** ✅
- [ ] state.py merged
- [ ] data_types.py merged
- [ ] agent.py merged
- [ ] git_ops.py merged
- [ ] workflow_ops.py merged
- [ ] All tests passing

**Phase 3: Configuration** ✅
- [ ] start.md updated
- [ ] test_e2e.md updated
- [ ] Dynamic ports working

**Phase 4: Testing** ✅
- [ ] Old workflows work
- [ ] New workflows work
- [ ] All features tested
- [ ] No breaking changes

---

### What You Now Have

**New Capabilities:**
1. ✅ **Meta-Command Generation** - System extends itself
2. ✅ **KPI Tracking** - System measures performance
3. ✅ **Worktree Isolation** - Foundation for 15x parallelism
4. ✅ **Dynamic Model Selection** - Cost optimization
5. ✅ **ISO Workflows** - Ready for parallel execution
6. ✅ **Enhanced State Management** - Tracks worktree, ports, model
7. ✅ **Retry Logic** - Better error handling
8. ✅ **Working Directory Support** - Enables worktree execution

**Quantitative Improvements:**
- Commands: 21 → 27 (+29%)
- Workflows: 12 → 26 (+117%)
- State fields: 5 → 10 (+100%)
- Capability levels: 0-1 → 3-4 (meta-agentic)

**Next Steps:**
1. Test iso workflows with real issues
2. Create worktrees for parallel execution
3. Enable ZTE for autonomous operation
4. Add learning-based features (Phase 5)

---

### Rollback Procedure (If Needed)

**If anything breaks:**

```bash
# View recent commits
git log --oneline -10

# Rollback to before migration
git reset --hard <commit-before-phase-1>

# Force push (CAUTION)
git push --force
```

**Selective Rollback:**
```bash
# Rollback specific file
git checkout HEAD~1 -- adws/adw_modules/agent.py

# Commit rollback
git commit -m "revert: Rollback agent.py changes"
```

---

### Success Metrics

**Immediate Value (Day 1):**
- [ ] Can generate new commands via `/meta-command`
- [ ] Can track performance via `/track_agentic_kpis`
- [ ] ISO workflows available for testing

**Short-Term Value (Week 1):**
- [ ] Model selection reduces costs on simple tasks
- [ ] Worktree isolation tested with 2-3 parallel workflows
- [ ] No regressions in existing functionality

**Long-Term Value (Month 1):**
- [ ] 5+ workflows running in parallel regularly
- [ ] 50%+ cost reduction on routine tasks
- [ ] KPI dashboard shows consistent improvement
- [ ] Team using meta-command to create custom workflows

---

### Time Tracking

**Planned vs Actual:**

| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | 30 min | _____ min | _____ |
| Phase 2 | 6 hours | _____ hours | _____ |
| Phase 3 | 30 min | _____ min | _____ |
| Phase 4 | 1 hour | _____ hour | _____ |
| **Total** | **8 hours** | **_____ hours** | **_____** |

---

### Notes & Issues

**Issues Encountered:**
-

**Workarounds Applied:**
-

**Unexpected Benefits:**
-

**Follow-Up Tasks:**
-

---

## Status: READY TO EXECUTE

✅ Plan documented
✅ Commands prepared
✅ Tests defined
✅ Rollback procedure ready

**Next Action:** Execute Phase 1 (30 minutes)

**Start Time:** __________
**End Time:** __________
