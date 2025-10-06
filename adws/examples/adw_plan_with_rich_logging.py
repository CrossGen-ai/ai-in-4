#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""
ADW Plan - Example with Rich Logging Integration

This is an example showing how to integrate Rich logging into an ADW workflow.
Compare this with the original adw_plan.py to see the improvements.
"""

import sys
from pathlib import Path

# Standard ADW imports
from adw_modules.agent import (
    run_slash_command,
    get_model_for_slash_command,
)
from adw_modules.state import ADWState
from adw_modules.data_types import AgentTemplateRequest

# Rich logging imports
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_error,
)


def main():
    """Main workflow function with Rich logging."""

    # Parse arguments
    if len(sys.argv) < 2:
        log_error("Missing required argument: issue-number")
        print("\nUsage: uv run adw_plan_with_rich_logging.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = int(sys.argv[1])
    adw_id = sys.argv[2] if len(sys.argv) > 2 else f"adw-{issue_number}"

    # ============================================================================
    # WORKFLOW START - Rich logging provides beautiful panel with issue info
    # ============================================================================
    log_workflow_start("adw_plan", adw_id, issue_number)

    try:
        # ========================================================================
        # STATE INITIALIZATION
        # ========================================================================
        state = ADWState(adw_id)
        state.update(issue_number=issue_number)
        state.save("adw_plan")

        # Log state update with visual indicator
        ADWLogger.state_update(adw_id, "issue_number", issue_number)

        # ========================================================================
        # ISSUE CLASSIFICATION
        # Before: logger.info(f"Classifying issue #{issue_number}")
        # After: Beautiful panel with command details
        # ========================================================================
        ADWLogger.separator("Issue Classification")

        # Log the slash command with full details
        ADWLogger.slash_command_start(
            "/classify_issue",
            [str(issue_number)],
            adw_id,
            model="sonnet"
        )

        classify_result = run_slash_command(
            "/classify_issue",
            adw_id,
            [str(issue_number)]
        )

        if not classify_result.success:
            raise Exception(f"Classification failed: {classify_result.error}")

        # Log successful completion
        ADWLogger.slash_command_complete(
            "/classify_issue",
            success=True,
            duration_seconds=classify_result.duration
        )

        issue_class = classify_result.data.get("issue_class", "/feature")
        state.update(issue_class=issue_class)
        state.save("adw_plan")

        # Log state update
        ADWLogger.state_update(adw_id, "issue_class", issue_class)

        # ========================================================================
        # BRANCH GENERATION
        # ========================================================================
        ADWLogger.separator("Branch Generation")

        ADWLogger.slash_command_start(
            "/generate_branch_name",
            [str(issue_number)],
            adw_id,
            model="sonnet"
        )

        branch_result = run_slash_command(
            "/generate_branch_name",
            adw_id,
            [str(issue_number)]
        )

        if not branch_result.success:
            raise Exception(f"Branch generation failed: {branch_result.error}")

        branch_name = branch_result.data.get("branch_name")
        state.update(branch_name=branch_name)
        state.save("adw_plan")

        # Log git operation with visual indicator
        ADWLogger.git_operation("Branch Generated", branch_name)
        ADWLogger.state_update(adw_id, "branch_name", branch_name)

        # ========================================================================
        # PLAN GENERATION
        # ========================================================================
        ADWLogger.separator("Plan Generation")

        # Get dynamic model selection
        request = AgentTemplateRequest(
            agent_name="planner",
            slash_command="/plan",
            args=[str(issue_number)],
            adw_id=adw_id
        )
        model = get_model_for_slash_command(request)

        # Log model selection with visual indicator
        model_set = state.get("model_set", "base")
        ADWLogger.model_selection("/plan", model_set, model)

        ADWLogger.slash_command_start(
            "/plan",
            [str(issue_number)],
            adw_id,
            model=model
        )

        plan_result = run_slash_command(
            "/plan",
            adw_id,
            [str(issue_number)],
            model=model
        )

        if not plan_result.success:
            raise Exception(f"Planning failed: {plan_result.error}")

        ADWLogger.slash_command_complete(
            "/plan",
            success=True,
            duration_seconds=plan_result.duration
        )

        plan_file = plan_result.data.get("plan_file")
        state.update(plan_file=plan_file)
        state.save("adw_plan")

        # Log file creation
        ADWLogger.tool_call("Write", file_path=plan_file)
        ADWLogger.state_update(adw_id, "plan_file", plan_file)

        # ========================================================================
        # PLAN COMMIT
        # ========================================================================
        ADWLogger.separator("Plan Commit")

        ADWLogger.slash_command_start(
            "/commit",
            [plan_file],
            adw_id,
            model="sonnet"
        )

        commit_result = run_slash_command(
            "/commit",
            adw_id,
            [plan_file]
        )

        if commit_result.success:
            commit_sha = commit_result.data.get("commit_sha", "unknown")
            ADWLogger.git_operation("Committed", f"{commit_sha[:7]} - Plan created")
        else:
            ADWLogger.warning("Commit failed, continuing anyway")

        # ========================================================================
        # WORKFLOW COMPLETION - Beautiful success panel
        # ========================================================================
        log_workflow_complete("adw_plan", adw_id, success=True)

        # Show final state summary
        final_state = {
            "ADW ID": adw_id,
            "Issue": f"#{issue_number}",
            "Issue Class": issue_class,
            "Branch": branch_name,
            "Plan File": plan_file,
        }
        ADWLogger.config_table("Workflow Summary", final_state)

    except Exception as e:
        # Beautiful error panel with exception details
        log_error(f"Workflow failed", e)
        log_workflow_complete("adw_plan", adw_id, success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
