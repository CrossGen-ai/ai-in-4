#!/usr/bin/env -S uv run
# /// script
# dependencies = ["rich"]
# ///

"""
Test script to demonstrate Rich logging output without requiring a GitHub issue.
This shows what the ADW workflow logs will look like with Rich formatting.
"""

import sys
from pathlib import Path

# Add parent directory to path to import rich_logging
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_error,
)


def main():
    """Demonstrate Rich logging patterns."""

    # Simulate workflow execution
    adw_id = "adw-demo-123"
    issue_number = 42

    # 1. Workflow start
    log_workflow_start("adw_plan", adw_id, issue_number)

    # 2. Classification section
    ADWLogger.separator("Issue Classification")
    ADWLogger.slash_command_start(
        "/classify_issue",
        ["42"],
        adw_id,
        model="sonnet"
    )
    ADWLogger.slash_command_complete("/classify_issue", success=True, duration_seconds=3.5)
    ADWLogger.state_update(adw_id, "issue_class", "/feature")

    # 3. Branch generation section
    ADWLogger.separator("Branch Generation")
    branch_name = "feature/42-add-dark-mode-toggle"
    ADWLogger.git_operation("Branch Created", branch_name)
    ADWLogger.state_update(adw_id, "branch_name", branch_name)

    # 4. Plan generation section
    ADWLogger.separator("Plan Generation")
    ADWLogger.model_selection("/plan", "base", "sonnet")
    plan_file = f"agents/{adw_id}/plan.md"
    ADWLogger.tool_call("Write", file_path=plan_file)
    ADWLogger.state_update(adw_id, "plan_file", plan_file)

    # 5. Commit section
    ADWLogger.separator("Plan Commit")
    commit_msg = "feat: Add dark mode toggle to settings"
    ADWLogger.git_operation("Committed", commit_msg)

    # 6. Show configuration table
    config = {
        "ADW ID": adw_id,
        "Issue": f"#{issue_number}",
        "Issue Class": "/feature",
        "Branch": branch_name,
        "Plan File": plan_file,
        "Model Set": "base",
    }
    ADWLogger.config_table("Workflow Summary", config)

    # 7. Show info and warning
    ADWLogger.info("Pushing branch to remote...")
    ADWLogger.warning("This is a test workflow - no actual changes made")

    # 8. Workflow complete
    log_workflow_complete("adw_plan", adw_id, success=True)

    print("\n" + "="*60)
    print("✅ Rich logging demonstration complete!")
    print("="*60)
    print("\nThis is what your ADW workflows will look like with Rich logging.")
    print("Compare this to standard logger.info() output - much more readable!")


if __name__ == "__main__":
    main()
