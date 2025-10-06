#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""Integration test for Phase 2 merged modules.

Tests the integration of:
- state.py: New fields and methods
- data_types.py: New types (ADWExtractionResult, ModelSet, RetryCode)
- agent.py: Model selection based on state
- git_ops.py: cwd parameter support
- workflow_ops.py: ADWExtractionResult return type
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.state import ADWState
from adw_modules.agent import get_model_for_slash_command
from adw_modules.data_types import AgentTemplateRequest

print("=" * 60)
print("Phase 2.6 Integration Test")
print("=" * 60)

# Test 1: Create state with all new fields
print("\n[Test 1] Create state with all new fields")
state = ADWState("integration")
state.update(
    worktree_path="/tmp/test-worktree",
    backend_port=9105,
    frontend_port=9205,
    model_set="heavy"
)
state.save("integration_test")
print(f"✓ State created with ID: integration")
print(f"  - worktree_path: {state.get('worktree_path')}")
print(f"  - backend_port: {state.get('backend_port')}")
print(f"  - frontend_port: {state.get('frontend_port')}")
print(f"  - model_set: {state.get('model_set')}")

# Test 2: Test working directory
print("\n[Test 2] Test get_working_directory() method")
working_dir = state.get_working_directory()
assert working_dir == "/tmp/test-worktree", f"Expected /tmp/test-worktree, got {working_dir}"
print(f"✓ Working directory: {working_dir}")

# Test 3: Test model selection with heavy model set
print("\n[Test 3] Test model selection (heavy mode)")
request = AgentTemplateRequest(
    agent_name="test",
    slash_command="/implement",
    args=["test.md"],
    adw_id="integration"
)
model = get_model_for_slash_command(request)
assert model == "opus", f"Expected opus for heavy /implement, got {model}"
print(f"✓ Model selected: {model} (heavy mode)")

# Test 4: Test model selection with base model set
print("\n[Test 4] Test model selection (base mode)")
state_base = ADWState("integration_base")
state_base.update(model_set="base")
state_base.save("integration_test")

request_base = AgentTemplateRequest(
    agent_name="test",
    slash_command="/implement",
    args=["test.md"],
    adw_id="integration_base"
)
model_base = get_model_for_slash_command(request_base)
assert model_base == "sonnet", f"Expected sonnet for base /implement, got {model_base}"
print(f"✓ Model selected: {model_base} (base mode)")

# Test 5: Test append_adw_id method
print("\n[Test 5] Test append_adw_id() method")
state.append_adw_id("adw_test_1")
state.append_adw_id("adw_test_2")
state.append_adw_id("adw_test_1")  # Duplicate
all_adws = state.get("all_adws")
assert len(all_adws) == 2, f"Expected 2 unique ADWs, got {len(all_adws)}"
assert "adw_test_1" in all_adws and "adw_test_2" in all_adws
print(f"✓ ADW tracking: {all_adws}")

# Test 6: Test git_ops cwd parameter (backward compatibility)
print("\n[Test 6] Test git_ops cwd parameter (backward compatibility)")
from adw_modules.git_ops import get_current_branch

# Should work without cwd (backward compatible)
branch = get_current_branch()
print(f"✓ get_current_branch() without cwd: {branch}")

# Should work with cwd
branch_with_cwd = get_current_branch(cwd=os.getcwd())
assert branch == branch_with_cwd, "Results should be identical"
print(f"✓ get_current_branch(cwd=...) with cwd: {branch_with_cwd}")

# Test 7: Test workflow_ops ADWExtractionResult
print("\n[Test 7] Test workflow_ops ADWExtractionResult")
from adw_modules.workflow_ops import extract_adw_info
from adw_modules.data_types import ADWExtractionResult

# Create a test extraction (will fail gracefully without real agent)
result = extract_adw_info("test adw_plan", "temp_test")
assert isinstance(result, ADWExtractionResult), "Should return ADWExtractionResult"
print(f"✓ extract_adw_info returns ADWExtractionResult")
print(f"  - Type: {type(result).__name__}")
print(f"  - Has workflow_command attr: {hasattr(result, 'workflow_command')}")
print(f"  - Has adw_id attr: {hasattr(result, 'adw_id')}")
print(f"  - Has model_set attr: {hasattr(result, 'model_set')}")

# Test 8: Test data_types new types exist
print("\n[Test 8] Test data_types new types exist")
from adw_modules.data_types import RetryCode, ModelSet

# Check RetryCode enum
assert hasattr(RetryCode, 'CLAUDE_CODE_ERROR'), "RetryCode should have CLAUDE_CODE_ERROR"
assert hasattr(RetryCode, 'NONE'), "RetryCode should have NONE"
print(f"✓ RetryCode enum has expected values")
print(f"  - CLAUDE_CODE_ERROR: {RetryCode.CLAUDE_CODE_ERROR}")
print(f"  - NONE: {RetryCode.NONE}")

# Check ModelSet type (it's a Literal, so just verify import works)
print(f"✓ ModelSet type imported successfully")

# Cleanup test state files
print("\n[Cleanup] Removing test state files")
for test_adw_id in ["integration", "integration_base"]:
    state_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "agents", test_adw_id, "adw_state.json"
    )
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"✓ Removed {state_file}")
        # Try to remove empty directories
        try:
            os.rmdir(os.path.dirname(state_file))
            os.rmdir(os.path.dirname(os.path.dirname(state_file)))
        except:
            pass

print("\n" + "=" * 60)
print("✅ All integration tests passed!")
print("=" * 60)
print("\nPhase 2 Integration Status:")
print("  ✓ state.py - New fields and methods working")
print("  ✓ data_types.py - New types available")
print("  ✓ agent.py - Model selection working")
print("  ✓ git_ops.py - cwd parameter backward compatible")
print("  ✓ workflow_ops.py - ADWExtractionResult working")
print("\nAll modules integrated successfully!")

sys.exit(0)
