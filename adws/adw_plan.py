#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""
ADW Plan - AI Developer Workflow for agentic planning

Usage:
  uv run adw_plan.py <issue-number> [adw-id]

Workflow:
1. Fetch GitHub issue details
2. Classify issue type (/chore, /bug, /feature)
3. Create feature branch
4. Generate implementation plan
5. Commit plan
6. Push and create/update PR
"""

import sys
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import create_branch, commit_changes, finalize_git_operations
from adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from adw_modules.workflow_ops import (
    classify_issue,
    build_plan,
    generate_branch_name,
    create_commit,
    format_issue_message,
    ensure_adw_id,
    AGENT_PLANNER,
)
from adw_modules.utils import setup_logger
from adw_modules.data_types import GitHubIssue, IssueClassSlashCommand

# Rich console logging
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_error,
)


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that all required environment variables are set."""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_PATH",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = "Error: Missing required environment variables:"
        if logger:
            logger.error(error_msg)
            for var in missing_vars:
                logger.error(f"  - {var}")
        else:
            print(error_msg, file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(adw_id, "adw_plan") if adw_id else None
    adw_id = ensure_adw_id(issue_number, adw_id, temp_logger)

    # Load the state that was created/found by ensure_adw_id
    state = ADWState.load(adw_id, temp_logger)

    # Ensure state has the adw_id field
    if not state.get("adw_id"):
        state.update(adw_id=adw_id)

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_plan")

    # Rich console: Workflow start
    log_workflow_start("adw_plan", adw_id, int(issue_number))
    logger.info(f"ADW Plan starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment
    check_env_vars(logger)

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        log_error("Error getting repository URL", e)
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Fetch issue details
    issue: GitHubIssue = fetch_issue(issue_number, repo_path)

    logger.debug(f"Fetched issue: {issue.model_dump_json(indent=2, by_alias=True)}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Starting planning phase")
    )

    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 🔍 Using state\n```json\n{json.dumps(state.data, indent=2)}\n```",
    )

    # Rich console: Issue classification section
    ADWLogger.separator("Issue Classification")

    # Classify the issue
    issue_command, error = classify_issue(issue, adw_id, logger)

    if error:
        log_error("Error classifying issue", Exception(error))
        logger.error(f"Error classifying issue: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Error classifying issue: {error}"),
        )
        sys.exit(1)

    state.update(issue_class=issue_command)
    state.save("adw_plan")
    ADWLogger.state_update(adw_id, "issue_class", issue_command)
    logger.info(f"Issue classified as: {issue_command}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Issue classified as: {issue_command}"),
    )

    # Rich console: Branch generation section
    ADWLogger.separator("Branch Generation")

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, adw_id, logger)

    if error:
        log_error("Error generating branch name", Exception(error))
        logger.error(f"Error generating branch name: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"❌ Error generating branch name: {error}"
            ),
        )
        sys.exit(1)

    # Create git branch
    success, error = create_branch(branch_name)

    if not success:
        log_error("Error creating branch", Exception(error))
        logger.error(f"Error creating branch: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Error creating branch: {error}"),
        )
        sys.exit(1)

    state.update(branch_name=branch_name)
    state.save("adw_plan")
    ADWLogger.git_operation("Branch Created", branch_name)
    ADWLogger.state_update(adw_id, "branch_name", branch_name)
    logger.info(f"Working on branch: {branch_name}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Working on branch: {branch_name}"),
    )

    # Rich console: Plan generation section
    ADWLogger.separator("Plan Generation")

    # Build the implementation plan
    logger.info("Building implementation plan")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, "✅ Building implementation plan"),
    )

    plan_response = build_plan(issue, issue_command, adw_id, logger)

    if not plan_response.success:
        log_error("Error building plan", Exception(plan_response.output))
        logger.error(f"Error building plan: {plan_response.output}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_PLANNER, f"❌ Error building plan: {plan_response.output}"
            ),
        )
        sys.exit(1)

    logger.debug(f"Plan response: {plan_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, "✅ Implementation plan created"),
    )

    # Get the plan file path directly from response
    logger.info("Getting plan file path")
    plan_file_path = plan_response.output.strip()
    
    # Validate the path exists
    if not plan_file_path:
        error = "No plan file path returned from planning agent"
        log_error(error, Exception(error))
        logger.error(error)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error}"),
        )
        sys.exit(1)

    if not os.path.exists(plan_file_path):
        error = f"Plan file does not exist: {plan_file_path}"
        log_error(error, Exception(error))
        logger.error(error)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error}"),
        )
        sys.exit(1)

    state.update(plan_file=plan_file_path)
    state.save("adw_plan")
    ADWLogger.tool_call("Write", file_path=plan_file_path)
    ADWLogger.state_update(adw_id, "plan_file", plan_file_path)
    logger.info(f"Plan file created: {plan_file_path}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Plan file created: {plan_file_path}"),
    )

    # Rich console: Commit section
    ADWLogger.separator("Plan Commit")

    # Create commit message
    logger.info("Creating plan commit")
    commit_msg, error = create_commit(
        AGENT_PLANNER, issue, issue_command, adw_id, logger
    )

    if error:
        log_error("Error creating commit message", Exception(error))
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_PLANNER, f"❌ Error creating commit message: {error}"
            ),
        )
        sys.exit(1)

    # Commit the plan
    success, error = commit_changes(commit_msg)

    if not success:
        log_error("Error committing plan", Exception(error))
        logger.error(f"Error committing plan: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_PLANNER, f"❌ Error committing plan: {error}"
            ),
        )
        sys.exit(1)

    ADWLogger.git_operation("Committed", commit_msg[:60] + "..." if len(commit_msg) > 60 else commit_msg)
    logger.info(f"Committed plan: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_PLANNER, "✅ Plan committed")
    )

    # Finalize git operations (push and PR)
    finalize_git_operations(state, logger)

    logger.info("Planning phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Planning phase completed")
    )

    # Save final state
    state.save("adw_plan")

    # Rich console: Workflow complete
    log_workflow_complete("adw_plan", adw_id, success=True)

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final planning state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )


if __name__ == "__main__":
    main()
