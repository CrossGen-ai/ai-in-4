#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""
ADW Test Iso - AI Developer Workflow for agentic testing in isolated worktrees

Usage:
  uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]

Workflow:
1. Load state and validate worktree exists
2. Run application test suite in worktree
3. Report results to issue
4. Create commit with test results in worktree
5. Push and update PR

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import json
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional, List
from dotenv import load_dotenv
from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    TestResult,
    E2ETestResult,
    IssueClassSlashCommand,
    TestEnsuranceReport,
)
from adw_modules.agent import execute_template
from adw_modules.github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    get_repo_url,
)
from adw_modules.utils import make_adw_id, setup_logger, parse_json, check_env_vars, format_issue_message
from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.workflow_ops import (
    create_commit,
    ensure_adw_id,
    classify_issue,
)
from adw_modules.worktree_ops import validate_worktree
from adw_modules.test_analysis import analyze_and_fix_test_failures, should_rerun_tests

# Rich console logging
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_error,
)

# Agent name constants
AGENT_TESTER = "test_runner"
AGENT_E2E_TESTER = "e2e_test_runner"
AGENT_BRANCH_GENERATOR = "branch_generator"

# Maximum number of test retry attempts after resolution
MAX_TEST_RETRY_ATTEMPTS = 4
MAX_E2E_TEST_RETRY_ATTEMPTS = 2  # E2E ui tests




def run_tests(adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None) -> AgentPromptResponse:
    """Run the test suite using the /test command."""
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=[],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    test_response = execute_template(test_template_request)

    logger.debug(
        f"test_response: {test_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return test_response


def parse_test_results(
    output: str, logger: logging.Logger
) -> Tuple[List[TestResult], int, int]:
    """Parse test results JSON and return (results, passed_count, failed_count)."""
    try:
        # Use parse_json to handle markdown-wrapped JSON
        results = parse_json(output, List[TestResult])

        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing test results: {e}")
        return [], 0, 0


def format_test_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format test results for GitHub issue comment with JSON blocks."""
    if not results:
        return "❌ No test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed Tests")
        comment_parts.append("")

        # Loop over each failed test
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests header
    if passed_tests:
        comment_parts.append("## ✅ Passed Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Summary
    comment_parts.append("## Summary")
    comment_parts.append(f"- **Passed**: {passed_count}")
    comment_parts.append(f"- **Failed**: {failed_count}")
    comment_parts.append(f"- **Total**: {len(results)}")

    return "\n".join(comment_parts)


def parse_e2e_test_results(
    output: str, logger: logging.Logger
) -> Tuple[List[E2ETestResult], int, int]:
    """Parse E2E test results JSON and return (results, passed_count, failed_count)."""
    try:
        # Use parse_json to handle markdown-wrapped JSON
        results = parse_json(output, List[E2ETestResult])

        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing E2E test results: {e}")
        return [], 0, 0


def post_comprehensive_test_summary(
    issue_number: str,
    adw_id: str,
    results: List[TestResult],
    e2e_results: List[E2ETestResult],
    logger: logging.Logger,
):
    """Post a comprehensive test summary including both unit and E2E tests."""
    summary = "# 🧪 Comprehensive Test Results\n\n"

    # Unit test section
    if results:
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        summary += "## Unit Tests\n\n"
        summary += f"- **Total**: {len(results)}\n"
        summary += f"- **Passed**: {passed_count} ✅\n"
        summary += f"- **Failed**: {failed_count} ❌\n\n"

        # List failures first
        failed_tests = [test for test in results if not test.passed]
        if failed_tests:
            summary += "### Failed Unit Tests:\n"
            for test in failed_tests:
                summary += f"- ❌ {test.test_name}\n"
            summary += "\n"

    # E2E test section
    if e2e_results:
        e2e_passed_count = sum(1 for test in e2e_results if test.passed)
        e2e_failed_count = len(e2e_results) - e2e_passed_count

        summary += "## E2E Tests\n\n"
        summary += f"- **Total**: {len(e2e_results)}\n"
        summary += f"- **Passed**: {e2e_passed_count} ✅\n"
        summary += f"- **Failed**: {e2e_failed_count} ❌\n\n"

        # List E2E failures
        e2e_failed_tests = [test for test in e2e_results if not test.passed]
        if e2e_failed_tests:
            summary += "### Failed E2E Tests:\n"
            for result in e2e_failed_tests:
                summary += f"- ❌ {result.test_name}\n"
                if result.screenshots:
                    summary += f"  - Screenshots: {', '.join(result.screenshots)}\n"

    # Overall status
    total_failures = (
        (failed_count if results else 0) + 
        (e2e_failed_count if e2e_results else 0)
    )
    if total_failures > 0:
        summary += f"\n### ❌ Overall Status: FAILED\n"
        summary += f"Total failures: {total_failures}\n"
    else:
        total_tests = len(results) + len(e2e_results)
        summary += f"\n### ✅ Overall Status: PASSED\n"
        summary += f"All {total_tests} tests passed successfully!\n"

    # Post the summary to the issue
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "test_summary", summary)
    )

    logger.info(f"Posted comprehensive test results summary to issue #{issue_number}")


def run_e2e_tests(adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None) -> AgentPromptResponse:
    """Run the E2E test suite using the /test_e2e command.
    
    Note: The test_e2e command will automatically detect and use ports from .ports.env
    in the working directory if it exists.
    """
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_E2E_TESTER,
        slash_command="/test_e2e",
        args=[],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"e2e_test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    test_response = execute_template(test_template_request)

    logger.debug(
        f"e2e_test_response: {test_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return test_response


def resolve_failed_tests(
    failed_tests: List[TestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """
    Attempt to resolve failed tests using the resolve_failed_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(
            f"\n=== Resolving failed test {idx + 1}/{len(failed_tests)}: {test.test_name} ==="
        )

        # Create payload for the resolve command
        test_payload = test.model_dump_json(indent=2)

        # Create agent name with iteration
        agent_name = f"test_resolver_iter{iteration}_{idx}"

        # Create template request with worktree_path
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_test",
            args=[test_payload],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"🔧 Attempting to resolve: {test.test_name}\n```json\n{test_payload}\n```",
            ),
        )

        # Execute resolution
        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"✅ Successfully resolved: {test.test_name}",
                ),
            )
            logger.info(f"Successfully resolved: {test.test_name}")
        else:
            unresolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ Failed to resolve: {test.test_name}",
                ),
            )
            logger.error(f"Failed to resolve: {test.test_name}")

    return resolved_count, unresolved_count


def run_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    max_attempts: int = MAX_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[TestResult], int, int, AgentPromptResponse]:
    """
    Run tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count, last_test_response).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0
    test_response = None

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== Test Run Attempt {attempt}/{max_attempts} ===")

        # Run tests in worktree
        test_response = run_tests(adw_id, logger, worktree_path)

        # If there was a high level - non-test related error, stop and report it
        if not test_response.success:
            logger.error(f"Error running tests: {test_response.output}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"❌ Error running tests: {test_response.output}",
                ),
            )
            break

        # Parse test results
        results, passed_count, failed_count = parse_test_results(
            test_response.output, logger
        )

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(f"Reached maximum retry attempts ({max_attempts}), stopping")
            break

        # If we have failed tests and this isn't the last attempt, try to resolve

        # NEW: Run Test Doctor analysis first (ISO mode with worktree)
        logger.info("\n=== Running Test Doctor Analysis (ISO Mode) ===")
        try:
            analysis = analyze_and_fix_test_failures(
                test_output=test_response.output,
                adw_id=adw_id,
                logger=logger,
                working_dir=worktree_path,  # ISO mode - use worktree path
                auto_fix=True,
            )

            logger.info(f"Test Doctor Analysis Complete (ISO):")
            logger.info(f"  - Total failures: {analysis['total_failures']}")
            logger.info(f"  - Known patterns: {analysis['known_patterns']}")
            logger.info(f"  - New patterns: {analysis['new_patterns']}")
            logger.info(f"  - Auto-fixes applied: {analysis['fixes_applied']}")
            logger.info(f"  - Worktree: {worktree_path}")

            # If fixes were applied, report and continue to re-run tests
            if analysis['fixes_applied'] > 0:
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "test_doctor",
                        f"🔬 Applied {analysis['fixes_applied']} auto-fixes from Test Doctor (ISO)",
                    ),
                )
                logger.info(f"\n=== Re-running tests after Test Doctor auto-fixes ===")
                continue
        except Exception as e:
            logger.warning(f"Test Doctor analysis failed: {e}")
            # Continue with existing resolution logic

        logger.info("\n=== Attempting to resolve failed tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"🔧 Found {failed_count} failed tests. Attempting resolution...",
            ),
        )

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_tests(
            failed_tests, adw_id, issue_number, logger, worktree_path, iteration=attempt
        )

        # Report resolution results
        if resolved > 0:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"✅ Resolved {resolved}/{failed_count} failed tests"
                ),
            )

            # Continue to next attempt if we resolved something
            logger.info(f"\n=== Re-running tests after resolving {resolved} tests ===")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"🔄 Re-running tests (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            # No tests were resolved, no point in retrying
            logger.info("No tests were resolved, stopping retry attempts")
            break

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count, test_response


def resolve_failed_e2e_tests(
    failed_tests: List[E2ETestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """
    Attempt to resolve failed E2E tests using the resolve_failed_e2e_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(
            f"\n=== Resolving failed E2E test {idx + 1}/{len(failed_tests)}: {test.test_name} ==="
        )

        # Create payload for the resolve command
        test_payload = test.model_dump_json(indent=2)

        # Create agent name with iteration
        agent_name = f"e2e_test_resolver_iter{iteration}_{idx}"

        # Create template request with worktree_path
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_e2e_test",
            args=[test_payload],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"🔧 Attempting to resolve E2E test: {test.test_name}\n```json\n{test_payload}\n```",
            ),
        )

        # Execute resolution
        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"✅ Successfully resolved E2E test: {test.test_name}",
                ),
            )
            logger.info(f"Successfully resolved E2E test: {test.test_name}")
        else:
            unresolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ Failed to resolve E2E test: {test.test_name}",
                ),
            )
            logger.error(f"Failed to resolve E2E test: {test.test_name}")

    return resolved_count, unresolved_count


def run_e2e_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    max_attempts: int = MAX_E2E_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[E2ETestResult], int, int]:
    """
    Run E2E tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== E2E Test Run Attempt {attempt}/{max_attempts} ===")

        # Run E2E tests (will auto-detect ports from .ports.env in worktree)
        e2e_response = run_e2e_tests(adw_id, logger, worktree_path)

        if not e2e_response.success:
            logger.error(f"Error running E2E tests: {e2e_response.output}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"❌ Error running E2E tests: {e2e_response.output}",
                ),
            )
            break

        # Parse E2E results
        results, passed_count, failed_count = parse_e2e_test_results(
            e2e_response.output, logger
        )

        if not results:
            logger.warning("No E2E test results to process")
            break

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All E2E tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(
                f"Reached maximum E2E retry attempts ({max_attempts}), stopping"
            )
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed E2E tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"🔧 Found {failed_count} failed E2E tests. Attempting resolution...",
            ),
        )

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_e2e_tests(
            failed_tests, adw_id, issue_number, logger, worktree_path, iteration=attempt
        )

        # Report resolution results
        if resolved > 0:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"✅ Resolved {resolved}/{failed_count} failed E2E tests",
                ),
            )

            # Continue to next attempt if we resolved something
            logger.info(
                f"\n=== Re-running E2E tests after resolving {resolved} tests ==="
            )
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"🔄 Re-running E2E tests (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            # No tests were resolved, no point in retrying
            logger.info("No E2E tests were resolved, stopping retry attempts")
            break

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count


# ====================================================================
# Test Ensurance System - Autonomous Test Creation and Validation (ISO)
# ====================================================================


def extract_test_requirements_with_ai(
    plan_file: str, adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None
) -> List[dict]:
    """
    Extract test requirements from plan file using AI (ISO version).
    Returns list of test requirements.
    """
    logger.info(f"Extracting test requirements from {plan_file}")

    request = AgentTemplateRequest(
        agent_name="test_requirements_extractor",
        slash_command="/extract_test_requirements",
        args=[plan_file],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"Failed to extract test requirements: {response.output}")
        return []

    try:
        requirements = parse_json(response.output, list)
        return requirements if requirements else []
    except Exception as e:
        logger.error(f"Error parsing test requirements: {e}")
        return []


def categorize_tests_fast(
    requirements: List[dict], logger: logging.Logger, working_dir: Optional[str] = None
) -> dict:
    """
    Fast Python categorization of test files (ISO version).
    Returns: {missing: [], obviously_broken: [], needs_validation: []}
    """
    import re

    result = {"missing": [], "obviously_broken": [], "needs_validation": []}

    for req in requirements:
        test_file = req.get("test_file_path")
        if not test_file:
            continue

        # Make path relative to working_dir if provided
        full_path = os.path.join(working_dir, test_file) if working_dir else test_file

        # Check 1: File exists?
        if not os.path.exists(full_path):
            logger.debug(f"  ✗ {test_file} - missing")
            result["missing"].append(req)
            continue

        # Check 2: Obviously broken?
        try:
            with open(full_path, "r") as f:
                content = f.read()

            is_broken = (
                len(content.strip()) < 10
                or not re.search(r"def test_\w+", content)
                or "assert" not in content
            )

            if is_broken:
                logger.debug(f"  ✗ {test_file} - obviously broken")
                req["content"] = content
                result["obviously_broken"].append(req)
            else:
                logger.debug(f"  ? {test_file} - needs validation")
                req["content"] = content
                req["quick_analysis"] = {
                    "has_imports": "import" in content,
                    "test_count": len(re.findall(r"def test_\w+", content)),
                    "assertion_count": content.count("assert"),
                }
                result["needs_validation"].append(req)
        except Exception as e:
            logger.error(f"Error reading {test_file}: {e}")
            result["missing"].append(req)

    return result


def validate_tests_batch_with_ai(
    tests_to_validate: List[dict], adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None
) -> List[dict]:
    """
    Validate existing tests against requirements using AI (ISO version - batched).
    Returns list of validation results.
    """
    if not tests_to_validate:
        return []

    logger.info(f"Validating {len(tests_to_validate)} test files with AI")

    batch_payload = {"tests_to_validate": tests_to_validate}

    request = AgentTemplateRequest(
        agent_name="test_batch_validator",
        slash_command="/validate_test_batch",
        args=[json.dumps(batch_payload, indent=2)],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"Failed to validate tests: {response.output}")
        return []

    try:
        validation_results = parse_json(response.output, list)
        return validation_results if validation_results else []
    except Exception as e:
        logger.error(f"Error parsing validation results: {e}")
        return []


def determine_actions(
    categorized: dict, validation_results: List[dict], logger: logging.Logger
) -> dict:
    """
    Determine what actions to take for each test file.
    Returns: {skip: [], create: [], replace: [], augment: []}
    """
    actions = {"skip": [], "create": [], "replace": [], "augment": []}

    actions["create"].extend(categorized.get("missing", []))
    actions["replace"].extend(categorized.get("obviously_broken", []))

    for result in validation_results:
        recommendation = result.get("recommendation", "complete")
        test_file = result.get("test_file_path")

        original_req = next(
            (
                req
                for req in categorized.get("needs_validation", [])
                if req.get("test_file_path") == test_file
            ),
            None,
        )

        if not original_req:
            continue

        original_req["validation_result"] = result

        if recommendation == "complete":
            actions["skip"].append(original_req)
        elif recommendation == "augment":
            actions["augment"].append(original_req)
        elif recommendation == "replace":
            actions["replace"].append(original_req)

    logger.debug(
        f"Actions determined - "
        f"skip: {len(actions['skip'])}, "
        f"create: {len(actions['create'])}, "
        f"replace: {len(actions['replace'])}, "
        f"augment: {len(actions['augment'])}"
    )

    return actions


def create_or_augment_test(
    action_type: str, req: dict, adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Create or augment a test file using AI (ISO version).
    Returns (success, test_file_path).
    """
    test_file = req.get("test_file_path")
    logger.info(f"{action_type.capitalize()}ing test: {test_file}")

    if action_type == "create":
        context = {
            "test_file_path": test_file,
            "source_file_path": req.get("source_file_path", ""),
            "description": req.get("description", ""),
            "test_scenarios": req.get("test_scenarios", []),
            "relevant_edge_cases": req.get("relevant_edge_cases", []),
            "testing_framework": "pytest",
        }

        source_file = req.get("source_file_path")
        if source_file:
            full_source_path = os.path.join(working_dir, source_file) if working_dir else source_file
            if os.path.exists(full_source_path):
                try:
                    with open(full_source_path, "r") as f:
                        context["source_code"] = f.read()
                except Exception as e:
                    logger.warning(f"Could not read source file {source_file}: {e}")
                    context["source_code"] = ""

        example_test = find_example_test(logger, working_dir)
        if example_test:
            context["example_test_code"] = example_test

        request = AgentTemplateRequest(
            agent_name=f"test_creator_{adw_id[:8]}",
            slash_command="/create_test",
            args=[json.dumps(context, indent=2)],
            adw_id=adw_id,
            working_dir=working_dir,
        )

    else:  # augment
        validation = req.get("validation_result", {})
        coverage = validation.get("coverage_analysis", {})

        context = {
            "test_file_path": test_file,
            "existing_test_code": req.get("content", ""),
            "missing_scenarios": coverage.get("missing_scenarios", []),
            "edge_cases": req.get("relevant_edge_cases", []),
            "issues_to_fix": validation.get("issues", []),
        }

        source_file = req.get("source_file_path")
        if source_file:
            full_source_path = os.path.join(working_dir, source_file) if working_dir else source_file
            if os.path.exists(full_source_path):
                try:
                    with open(full_source_path, "r") as f:
                        context["source_code"] = f.read()
                except Exception as e:
                    logger.warning(f"Could not read source file {source_file}: {e}")
                    context["source_code"] = ""

        request = AgentTemplateRequest(
            agent_name=f"test_augmentor_{adw_id[:8]}",
            slash_command="/augment_test",
            args=[json.dumps(context, indent=2)],
            adw_id=adw_id,
            working_dir=working_dir,
        )

    response = execute_template(request)

    if response.success:
        return True, test_file
    else:
        logger.error(f"Failed to {action_type} test {test_file}: {response.output}")
        return False, test_file


def find_example_test(logger: logging.Logger, working_dir: Optional[str] = None) -> Optional[str]:
    """Find an example test file to use as a pattern (ISO version)."""
    import glob

    example_paths = [
        "app/server/tests/test_health.py",
        "app/server/tests/test_api.py",
    ]

    # Adjust paths for working_dir
    if working_dir:
        example_paths = [os.path.join(working_dir, p) for p in example_paths]
        search_pattern = os.path.join(working_dir, "app/server/tests/test_*.py")
    else:
        search_pattern = "app/server/tests/test_*.py"

    test_files = glob.glob(search_pattern)

    for path in example_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return f.read()
            except Exception as e:
                logger.debug(f"Could not read example {path}: {e}")

    for path in test_files:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return f.read()
            except Exception as e:
                logger.debug(f"Could not read example {path}: {e}")

    logger.warning("No example test files found")
    return None


def execute_test_actions_parallel(
    actions: dict, adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None, max_workers: int = 5
) -> dict:
    """
    Execute create/augment actions in parallel (ISO version).
    Returns: {created: [], augmented: [], failed: []}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {"created": [], "augmented": [], "failed": []}

    tasks = []
    for req in actions.get("create", []):
        tasks.append(("create", req))
    for req in actions.get("augment", []):
        tasks.append(("augment", req))
    for req in actions.get("replace", []):
        tasks.append(("create", req))

    if not tasks:
        return results

    logger.info(f"Executing {len(tasks)} test creation/augmentation tasks")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                create_or_augment_test, action_type, req, adw_id, logger, working_dir
            ): (action_type, req)
            for action_type, req in tasks
        }

        for future in as_completed(futures):
            action_type, req = futures[future]
            try:
                success, test_file = future.result()
                if success:
                    # Map action_type to result key
                    if action_type == "create":
                        result_key = "created"
                        action_past = "created"
                    elif action_type == "augment":
                        result_key = "augmented"
                        action_past = "augmented"
                    else:
                        result_key = "failed"
                        action_past = action_type

                    results[result_key].append(test_file)
                    logger.info(f"  ✓ {action_past} {test_file}")
                else:
                    results["failed"].append(test_file)
                    logger.error(f"  ✗ Failed to {action_type} {test_file}")
            except Exception as e:
                logger.error(f"  ✗ Exception during {action_type}: {e}")
                results["failed"].append(req.get("test_file_path", "unknown"))

    return results


def validate_and_fix_created_tests(
    execution_results: dict, adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None, max_fix_attempts: int = 2
) -> dict:
    """
    Run pytest on created tests and attempt to fix failures (ISO version).
    Returns: {created_and_passing: [], augmented_and_passing: [], created_but_failing: []}
    """
    validated = {
        "created_and_passing": [],
        "augmented_and_passing": [],
        "created_but_failing": [],
    }

    all_tests = execution_results.get("created", []) + execution_results.get("augmented", [])

    for test_file in all_tests:
        action_type = (
            "created" if test_file in execution_results.get("created", []) else "augmented"
        )

        logger.info(f"Validating {test_file}...")

        # Make path relative to working_dir for test command
        full_test_path = os.path.join(working_dir, test_file) if working_dir else test_file

        # Determine test command based on file type
        if test_file.endswith((".ts", ".tsx")):
            # Frontend TypeScript test - use vitest
            # For vitest, we need to be in the client directory
            if "app/client" in test_file:
                test_cwd = os.path.join(working_dir, "app/client") if working_dir else "app/client"
                relative_test_path = test_file.replace("app/client/", "")
            else:
                test_cwd = working_dir
                relative_test_path = test_file
            test_cmd = ["yarn", "test", relative_test_path]
        else:
            # Backend Python test - use pytest
            test_cwd = working_dir
            test_cmd = ["uv", "run", "pytest", full_test_path, "-v", "--tb=short"]

        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            cwd=test_cwd,
        )

        if result.returncode == 0:
            validated[f"{action_type}_and_passing"].append(test_file)
            logger.info(f"  ✓ All tests passing in {test_file}")
        else:
            logger.warning(f"  ✗ Tests failing in {test_file}, attempting fix...")

            fixed = attempt_test_fix(
                test_file,
                result.stdout + "\n" + result.stderr,
                adw_id,
                logger,
                working_dir,
                max_fix_attempts,
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
    working_dir: Optional[str] = None,
    max_attempts: int = 2,
) -> bool:
    """Attempt to fix failing test with AI (ISO version)."""

    for attempt in range(1, max_attempts + 1):
        logger.info(f"Fix attempt {attempt}/{max_attempts} for {test_file}...")

        full_test_path = os.path.join(working_dir, test_file) if working_dir else test_file

        try:
            with open(full_test_path, "r") as f:
                test_code = f.read()
        except Exception as e:
            logger.error(f"Could not read test file {test_file}: {e}")
            return False

        context = {
            "test_file_path": test_file,
            "test_code": test_code,
            "error_output": error_output,
        }

        request = AgentTemplateRequest(
            agent_name=f"test_fixer_{attempt}",
            slash_command="/fix_test",
            args=[json.dumps(context, indent=2)],
            adw_id=adw_id,
            working_dir=working_dir,
        )

        response = execute_template(request)

        if not response.success:
            logger.error(f"Fix attempt {attempt} failed: {response.output}")
            continue

        # Determine test command based on file type
        if test_file.endswith((".ts", ".tsx")):
            # Frontend TypeScript test - use vitest
            if "app/client" in test_file:
                test_cwd = os.path.join(working_dir, "app/client") if working_dir else "app/client"
                relative_test_path = test_file.replace("app/client/", "")
            else:
                test_cwd = working_dir
                relative_test_path = test_file
            test_cmd = ["yarn", "test", relative_test_path]
        else:
            # Backend Python test - use pytest
            test_cwd = working_dir
            test_cmd = ["uv", "run", "pytest", full_test_path, "-v"]

        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            cwd=test_cwd,
        )

        if result.returncode == 0:
            logger.info(f"Fix successful on attempt {attempt}")
            return True

        error_output = result.stdout + "\n" + result.stderr

    return False


def format_test_ensurance_report(report: TestEnsuranceReport, adw_id: str) -> str:
    """Format test ensurance report for GitHub comment."""
    summary = f"## ✅ Test Creation Complete ({adw_id})\n\n"

    summary += f"**Test Files Required:** {report.total_required}\n"
    summary += f"**Already Complete:** {report.already_complete} ✓\n"

    if report.created > 0:
        summary += f"**Created:** {report.created} ✓\n"

    if report.augmented > 0:
        summary += f"**Augmented:** {report.augmented} ✓\n"

    if report.failed > 0:
        summary += f"**Failed:** {report.failed} ❌\n"

    if report.all_passing:
        summary += f"\n### ✅ All created/augmented tests passing\n"
    else:
        summary += f"\n### ❌ Some tests failed validation\n"

    return summary


def ensure_tests_exist_and_complete(
    plan_file: str, adw_id: str, issue_number: str, logger: logging.Logger, working_dir: Optional[str] = None
) -> TestEnsuranceReport:
    """
    Ensure all planned tests exist and are complete (ISO version).
    Returns report of actions taken.
    """
    logger.info("=== Test Ensurance Phase (ISO) ===")

    # STEP 1: Extract requirements (AI - 1 call)
    logger.info("Step 1: Extracting test requirements from plan...")
    requirements = extract_test_requirements_with_ai(plan_file, adw_id, logger, working_dir)
    logger.info(f"Found {len(requirements)} test files in plan")

    if not requirements:
        logger.info("No test files specified in plan, skipping test ensurance")
        return TestEnsuranceReport(
            total_required=0,
            already_complete=0,
            created=0,
            augmented=0,
            failed=0,
            all_passing=True,
        )

    # STEP 2: Fast Python pre-filter
    logger.info("Step 2: Categorizing tests...")
    categorized = categorize_tests_fast(requirements, logger, working_dir)
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
            categorized["needs_validation"], adw_id, logger, working_dir
        )

    # STEP 4: Determine actions
    logger.info("Step 4: Determining actions...")
    actions = determine_actions(categorized, validation_results, logger)

    # Report to GitHub
    analysis_msg = f"📊 Test Validation Results:\n"
    analysis_msg += f"• {len(requirements)} test files required by plan\n"
    analysis_msg += f"• {len(actions['skip'])} tests complete and correct ✓\n"
    if actions["create"]:
        analysis_msg += f"• {len(actions['create'])} tests missing (will create)\n"
    if actions["augment"]:
        analysis_msg += f"• {len(actions['augment'])} tests incomplete (will augment)\n"
    if actions["replace"]:
        analysis_msg += f"• {len(actions['replace'])} tests broken (will replace)\n"

    make_issue_comment(
        issue_number, format_issue_message(adw_id, "test_creator", analysis_msg)
    )

    # Check if any actions needed
    actions_needed = (
        len(actions["create"]) > 0
        or len(actions["augment"]) > 0
        or len(actions["replace"]) > 0
    )

    # STEP 5: Execute actions (parallel)
    if actions_needed:
        logger.info("Step 5: Creating/augmenting tests...")
        execution_results = execute_test_actions_parallel(actions, adw_id, logger, working_dir)
    else:
        logger.info("Step 5: No test creation needed - all tests complete")
        execution_results = {"created": [], "augmented": [], "failed": []}

    # STEP 6: Validate created tests
    if execution_results["created"] or execution_results["augmented"]:
        logger.info("Step 6: Validating created tests...")
        validated = validate_and_fix_created_tests(execution_results, adw_id, logger, working_dir)
    else:
        validated = {
            "created_and_passing": [],
            "augmented_and_passing": [],
            "created_but_failing": [],
        }

    # Build report
    report = TestEnsuranceReport(
        total_required=len(requirements),
        already_complete=len(actions.get("skip", []))
        + len([r for r in validation_results if r.get("status") == "complete"]),
        created=len(validated["created_and_passing"]),
        augmented=len(validated["augmented_and_passing"]),
        failed=len(validated["created_but_failing"]) + len(execution_results.get("failed", [])),
        all_passing=len(validated["created_but_failing"]) == 0
        and len(execution_results.get("failed", [])) == 0,
    )

    logger.info(
        f"Test ensurance complete: "
        f"{report.created} created, "
        f"{report.augmented} augmented, "
        f"{report.already_complete} already complete"
    )

    return report


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Check for --skip-e2e flag in args
    skip_e2e = "--skip-e2e" in sys.argv
    # Remove flag from args if present
    if skip_e2e:
        sys.argv.remove("--skip-e2e")
    
    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]")
        print("\nError: adw-id is required to locate the worktree")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_test_iso")
    state = ADWState.load(adw_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"🔍 Found existing state - starting isolated testing\n```json\n{json.dumps(state.data, indent=2)}\n```")
        )
    else:
        # No existing state found
        logger = setup_logger(adw_id, "adw_test_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        sys.exit(1)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_test_iso")
    
    # Set up logger with ADW ID from command line
    logger = setup_logger(adw_id, "adw_test_iso")

    # Rich console: Workflow start
    log_workflow_start("adw_test_iso", adw_id, int(issue_number))
    logger.info(f"ADW Test Iso starting - ID: {adw_id}, Issue: {issue_number}, Skip E2E: {skip_e2e}")
    
    # Validate environment
    check_env_vars(logger)
    
    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
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
    
    # Get port information for display
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")
    
    make_issue_comment(
        issue_number, 
        format_issue_message(adw_id, "ops", f"✅ Starting isolated testing phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}\n"
                           f"🧪 E2E Tests: {'Skipped' if skip_e2e else 'Enabled'}")
    )
    
    # Track results for resolution attempts
    test_results = []
    e2e_results = []

    # NEW: Test Ensurance Phase (autonomous test creation) - ISO version
    spec_file = state.get("plan_file")
    if spec_file:
        # Make spec_file path relative to worktree
        full_spec_path = os.path.join(worktree_path, spec_file) if not os.path.isabs(spec_file) else spec_file

        if os.path.exists(full_spec_path):
            ADWLogger.separator("Test Ensurance (ISO)")
            logger.info("\n=== Test Ensurance Phase (ISO) ===")

            report = ensure_tests_exist_and_complete(
                plan_file=spec_file,
                adw_id=adw_id,
                issue_number=issue_number,
                logger=logger,
                working_dir=worktree_path,
            )

            # Report results to GitHub
            if report.created > 0 or report.augmented > 0:
                make_issue_comment(
                    issue_number, format_test_ensurance_report(report, adw_id)
                )

                # Commit the new/updated tests in the worktree
                logger.info("Committing created/augmented tests in worktree...")
                import glob
                import time

                test_files = glob.glob(os.path.join(worktree_path, "app/server/tests/test_*.py"))
                commit_files = []
                for tf in test_files:
                    if os.path.exists(tf):
                        mtime = os.path.getmtime(tf)
                        if time.time() - mtime < 60:  # Modified in last 60 seconds
                            commit_files.append(tf)

                if commit_files:
                    commit_msg = f"test_creator: feature: add/update unit tests (ISO)\n\n"
                    commit_msg += f"- Created: {report.created} test files\n"
                    commit_msg += f"- Augmented: {report.augmented} test files\n"
                    commit_msg += f"- All created tests passing: {report.all_passing}\n\n"
                    commit_msg += (
                        "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
                    )
                    commit_msg += "Co-Authored-By: Claude <noreply@anthropic.com>"

                    success, error = commit_changes(commit_msg, cwd=worktree_path)
                    if success:
                        logger.info("Test files committed successfully in worktree")
                    else:
                        logger.warning(f"Failed to commit test files: {error}")
        else:
            logger.info(f"Plan file not found at {full_spec_path}, skipping test ensurance")
    else:
        logger.info("No plan file found in state, skipping test ensurance phase")

    # Run unit tests (executing in worktree)
    logger.info("Running unit tests in worktree with automatic resolution")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "🧪 Running unit tests in isolated environment...")
    )
    
    # Run tests with resolution and retry logic
    results, passed_count, failed_count, test_response = run_tests_with_resolution(
        adw_id, issue_number, logger, worktree_path
    )
    
    # Track results
    test_results = results
    
    if results:
        comment = format_test_results_comment(results, passed_count, failed_count)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, comment)
        )
        logger.info(f"Test results: {passed_count} passed, {failed_count} failed")
    else:
        logger.warning("No test results found in output")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_TESTER, "⚠️ No test results found in output"
            ),
        )
    
    # Run E2E tests if not skipped (executing in worktree)
    e2e_passed = 0
    e2e_failed = 0
    if not skip_e2e:
        logger.info("Running E2E tests in worktree with automatic resolution")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_E2E_TESTER, "🌐 Running E2E tests in isolated environment...")
        )
        
        # Run E2E tests with resolution and retry logic
        e2e_results, e2e_passed, e2e_failed = run_e2e_tests_with_resolution(
            adw_id, issue_number, logger, worktree_path
        )
        
        if e2e_results:
            logger.info(f"E2E test results: {e2e_passed} passed, {e2e_failed} failed")
    
    # Post comprehensive summary
    post_comprehensive_test_summary(
        issue_number, adw_id, test_results, e2e_results, logger
    )
    
    # Check if we should exit due to test failures
    total_failures = failed_count + (e2e_failed if not skip_e2e and e2e_results else 0)
    if total_failures > 0:
        logger.warning(f"Tests completed with {total_failures} failures - continuing to commit results")
        # Note: We don't exit here anymore, we commit the results regardless
        # This is different from the old workflow which would exit(1) on failures
    
    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        issue_command, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/feature"
            logger.warning("Defaulting to /feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("adw_test_iso")
    
    # Create commit message
    logger.info("Creating test commit")
    commit_msg, error = create_commit(AGENT_TESTER, issue, issue_command, adw_id, logger, worktree_path)
    
    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)
    
    # Commit the test results (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)
    
    if not success:
        logger.error(f"Error committing test results: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, f"❌ Error committing test results: {error}")
        )
        sys.exit(1)
    
    logger.info(f"Committed test results: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_TESTER, "✅ Test results committed")
    )
    
    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    logger.info("Isolated testing phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Isolated testing phase completed")
    )
    
    # Save final state
    state.save("adw_test_iso")
    

    # Rich console: Workflow complete
    log_workflow_complete("adw_test_iso", adw_id, success=True)
    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"📋 Final test state:\n```json\n{json.dumps(state.data, indent=2)}\n```")
    )
    
    # Exit with appropriate code based on test results
    if total_failures > 0:
        logger.error(f"Test workflow completed with {total_failures} failures")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Test workflow completed with {total_failures} failures")
        )
        sys.exit(1)
    else:
        logger.info("All tests passed successfully")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", "✅ All tests passed successfully!")
        )


if __name__ == "__main__":
    main()