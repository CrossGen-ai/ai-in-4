#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""
ADW Build Iso - AI Developer Workflow for agentic building in isolated worktrees

Usage: 
  uv run adw_build_iso.py <issue-number> <adw-id>

Workflow:
1. Load state and validate worktree exists
2. Find existing plan (from state)
3. Implement the solution based on plan in worktree
4. Commit implementation in worktree
5. Push and update PR

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations, get_current_branch
from adw_modules.github import fetch_issue, make_issue_comment, get_repo_url, extract_repo_path
from adw_modules.workflow_ops import (
    implement_plan,
    create_commit,
    format_issue_message,
    AGENT_IMPLEMENTOR,
)
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.data_types import GitHubIssue
from adw_modules.worktree_ops import validate_worktree

# Rich console logging
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_error,
)




def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run adw_build_iso.py <issue-number> <adw-id>")
        print("\nError: adw-id is required to locate the worktree and plan file")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_build_iso")
    state = ADWState.load(adw_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🔍 Found existing state - resuming isolated build\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )
    else:
        # No existing state found
        logger = setup_logger(adw_id, "adw_build_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run adw_plan_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py first to create the worktree and state")
        sys.exit(1)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_build_iso")
    
    # Set up logger with ADW ID from command line
    logger = setup_logger(adw_id, "adw_build_iso")

    # Rich console: Workflow start
    log_workflow_start("adw_build_iso", adw_id, int(issue_number))
    logger.info(f"ADW Build Iso starting - ID: {adw_id}, Issue: {issue_number}")
    
    # Validate environment
    check_env_vars(logger)
    
    # Rich console: Worktree validation section
    ADWLogger.separator("Worktree Validation")

    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        log_error("Worktree validation failed", Exception(error))
        logger.error(f"Worktree validation failed: {error}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Worktree validation failed: {error}\n"
                               "Run adw_plan_iso.py or adw_patch_iso.py first")
        )
        sys.exit(1)
    
    # Get worktree path for explicit context
    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")
    
    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        log_error("Error getting repository URL", e)
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # Ensure we have required state fields
    if not state.get("branch_name"):
        error_msg = "No branch name in state - run adw_plan_iso.py first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    if not state.get("plan_file"):
        error_msg = "No plan file in state - run adw_plan_iso.py first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    # Rich console: Branch checkout section
    ADWLogger.separator("Branch Checkout")

    # Checkout the branch in the worktree
    branch_name = state.get("branch_name")
    result = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True, cwd=worktree_path)
    if result.returncode != 0:
        log_error("Failed to checkout branch in worktree", Exception(result.stderr))
        logger.error(f"Failed to checkout branch {branch_name} in worktree: {result.stderr}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Failed to checkout branch {branch_name} in worktree")
        )
        sys.exit(1)
    ADWLogger.git_operation("Checked Out", branch_name)
    logger.info(f"Checked out branch in worktree: {branch_name}")
    
    # Get the plan file from state
    plan_file = state.get("plan_file")
    logger.info(f"Using plan file: {plan_file}")
    
    # Get port information for display
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")
    
    make_issue_comment(
        issue_number, 
        format_issue_message(adw_id, "ops", f"✅ Starting isolated implementation phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}")
    )

    # Rich console: Implementation section
    ADWLogger.separator("Solution Implementation")

    # Implement the plan (executing in worktree)
    logger.info("Implementing solution in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementing solution in isolated environment")
    )
    
    implement_response = implement_plan(plan_file, adw_id, logger, working_dir=worktree_path)

    if not implement_response.success:
        log_error("Error implementing solution", Exception(implement_response.output))
        logger.error(f"Error implementing solution: {implement_response.output}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Error implementing solution: {implement_response.output}")
        )
        sys.exit(1)
    
    logger.debug(f"Implementation response: {implement_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Solution implemented")
    )
    
    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        from adw_modules.workflow_ops import classify_issue
        issue_command, error = classify_issue(issue, adw_id, logger)
        if error:
            log_error("Error classifying issue", Exception(error))
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/feature"
            logger.warning("Defaulting to /feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("adw_build_iso")

    # Rich console: Commit section
    ADWLogger.separator("Implementation Commit")

    # Create commit message
    logger.info("Creating implementation commit")
    commit_msg, error = create_commit(AGENT_IMPLEMENTOR, issue, issue_command, adw_id, logger, worktree_path)

    if error:
        log_error("Error creating commit message", Exception(error))
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)

    # Commit the implementation (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)

    if not success:
        log_error("Error committing implementation", Exception(error))
        logger.error(f"Error committing implementation: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Error committing implementation: {error}")
        )
        sys.exit(1)

    ADWLogger.git_operation("Committed", commit_msg[:60] + "..." if len(commit_msg) > 60 else commit_msg)
    logger.info(f"Committed implementation: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementation committed")
    )
    
    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    logger.info("Isolated implementation phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Isolated implementation phase completed")
    )
    
    # Save final state
    state.save("adw_build_iso")

    # Rich console: Workflow complete
    log_workflow_complete("adw_build_iso", adw_id, success=True)

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final build state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )


if __name__ == "__main__":
    main()