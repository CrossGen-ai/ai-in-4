#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""
ADW Test - AI Developer Workflow for agentic testing

Usage:
  uv run adw_test.py <issue-number> [adw-id] [--skip-e2e]

Workflow:
1. Fetch GitHub issue details (if not in state)
2. Run application test suite
3. Report results to issue
4. Create commit with test results
5. Push and update PR

Environment Requirements:
- ANTHROPIC_API_KEY: Anthropic API key
- CLAUDE_CODE_PATH: Path to Claude CLI
- GITHUB_PAT: (Optional) GitHub Personal Access Token - only if using a different account than 'gh auth login'
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
from adw_modules.utils import make_adw_id, setup_logger, parse_json, check_env_vars
from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.workflow_ops import (
    format_issue_message,
    create_commit,
    ensure_adw_id,
    classify_issue,
)

# Rich console logging
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_error,
)

# Removed create_or_find_branch - now using state directly

# Agent name constants
AGENT_TESTER = "test_runner"
AGENT_E2E_TESTER = "e2e_test_runner"
AGENT_BRANCH_GENERATOR = "branch_generator"

# Maximum number of test retry attempts after resolution
MAX_TEST_RETRY_ATTEMPTS = 4
MAX_E2E_TEST_RETRY_ATTEMPTS = 2  # E2E ui tests


def parse_args(
    state: Optional[ADWState] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[str], Optional[str], bool]:
    """Parse command line arguments.
    Returns (issue_number, adw_id, skip_e2e) where issue_number and adw_id may be None.
    """
    skip_e2e = False

    # Check for --skip-e2e flag in args
    if "--skip-e2e" in sys.argv:
        skip_e2e = True
        sys.argv.remove("--skip-e2e")

    # If we have state from stdin, we might not need issue number from args
    if state:
        # In piped mode, we might have no args at all
        if len(sys.argv) >= 2:
            # If an issue number is provided, use it
            return sys.argv[1], None, skip_e2e
        else:
            # Otherwise, we'll get issue from state
            return None, None, skip_e2e

    # Standalone mode - need at least issue number
    if len(sys.argv) < 2:
        usage_msg = [
            "Usage:",
            "  Standalone: uv run adw_test.py <issue-number> [adw-id] [--skip-e2e]",
            "  Chained: ... | uv run adw_test.py [--skip-e2e]",
            "Examples:",
            "  uv run adw_test.py 123",
            "  uv run adw_test.py 123 abc12345",
            "  uv run adw_test.py 123 --skip-e2e",
            '  echo \'{"issue_number": "123"}\' | uv run adw_test.py',
        ]
        if logger:
            for msg in usage_msg:
                logger.error(msg)
        else:
            for msg in usage_msg:
                print(msg)
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    return issue_number, adw_id, skip_e2e


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking."""
    if session_id:
        return f"{adw_id}_{agent_name}_{session_id}: {message}"
    return f"{adw_id}_{agent_name}: {message}"


def log_test_results(
    state: ADWState,
    results: List[TestResult],
    e2e_results: List[E2ETestResult],
    logger: logging.Logger,
) -> None:
    """Log comprehensive test results summary to the issue."""
    issue_number = state.get("issue_number")
    adw_id = state.get("adw_id")

    if not issue_number:
        logger.warning("No issue number in state, skipping test results logging")
        return

    # Calculate counts
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    e2e_passed_count = sum(1 for r in e2e_results if r.passed)
    e2e_failed_count = len(e2e_results) - e2e_passed_count

    # Create comprehensive summary
    summary = f"## 📊 Test Run Summary\n\n"

    # Unit tests summary
    summary += f"### Unit Tests\n"
    summary += f"**Total Tests:** {len(results)}\n"
    summary += f"**Passed:** {passed_count} ✅\n"
    summary += f"**Failed:** {failed_count} ❌\n\n"

    if results:
        summary += "#### Details:\n"
        for result in results:
            status = "✅" if result.passed else "❌"
            summary += f"- {status} **{result.test_name}**\n"
            if not result.passed and result.error:
                summary += f"  - Error: {result.error[:200]}...\n"

    # E2E tests summary if they were run
    if e2e_results:
        summary += f"\n### E2E Tests\n"
        summary += f"**Total Tests:** {len(e2e_results)}\n"
        summary += f"**Passed:** {e2e_passed_count} ✅\n"
        summary += f"**Failed:** {e2e_failed_count} ❌\n\n"

        summary += "#### Details:\n"
        for result in e2e_results:
            status = "✅" if result.passed else "❌"
            summary += f"- {status} **{result.test_name}**\n"
            if not result.passed and result.error:
                summary += f"  - Error: {result.error[:200]}...\n"
            if result.screenshots:
                summary += f"  - Screenshots: {', '.join(result.screenshots)}\n"

    # Overall status
    total_failures = failed_count + e2e_failed_count
    if total_failures > 0:
        summary += f"\n### ❌ Overall Status: FAILED\n"
        summary += f"Total failures: {total_failures}\n"
    else:
        summary += f"\n### ✅ Overall Status: PASSED\n"
        summary += f"All {len(results) + len(e2e_results)} tests passed successfully!\n"

    # Post the summary to the issue
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "test_summary", summary)
    )

    logger.info(f"Posted comprehensive test results summary to issue #{issue_number}")


def run_tests(adw_id: str, logger: logging.Logger) -> AgentPromptResponse:
    """Run the test suite using the /test command."""
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=[],
        adw_id=adw_id,
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

    # Remove trailing empty line
    if comment_parts and comment_parts[-1] == "":
        comment_parts.pop()

    return "\n".join(comment_parts)


def resolve_failed_tests(
    failed_tests: List[TestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
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

        # Create template request
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_test",
            args=[test_payload],
            adw_id=adw_id,
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"❌ Attempting to resolve: {test.test_name}\n```json\n{test_payload}\n```",
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

        # Run tests
        test_response = run_tests(adw_id, logger)

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
        logger.info("\n=== Attempting to resolve failed tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"❌ Found {failed_count} failed tests. Attempting resolution...",
            ),
        )

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_tests(
            failed_tests, adw_id, issue_number, logger, iteration=attempt
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


def run_e2e_tests(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    attempt: int = 1,
) -> List[E2ETestResult]:
    """Run all E2E tests found in .claude/commands/e2e/*.md sequentially."""
    import glob

    # Find all E2E test files
    e2e_test_files = glob.glob(".claude/commands/e2e/*.md")
    logger.info(f"Found {len(e2e_test_files)} E2E test files")

    if not e2e_test_files:
        logger.warning("No E2E test files found in .claude/commands/e2e/")
        return []

    results = []

    # Run tests sequentially
    for idx, test_file in enumerate(e2e_test_files):
        agent_name = f"{AGENT_E2E_TESTER}_{attempt - 1}_{idx}"
        result = execute_single_e2e_test(
            test_file, agent_name, adw_id, issue_number, logger
        )
        if result:
            results.append(result)
            # Break on first failure
            if not result.passed:
                logger.info(f"E2E test failed: {result.test_name}, stopping execution")
                break

    return results


def execute_single_e2e_test(
    test_file: str,
    agent_name: str,
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
) -> Optional[E2ETestResult]:
    """Execute a single E2E test and return the result."""
    test_name = os.path.basename(test_file).replace(".md", "")
    logger.info(f"Running E2E test: {test_name}")

    # Make issue comment
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, agent_name, f"✅ Running E2E test: {test_name}"),
    )

    # Create template request
    request = AgentTemplateRequest(
        agent_name=agent_name,
        slash_command="/test_e2e",
        args=[
            adw_id,
            agent_name,
            test_file,
        ],  # Pass ADW ID and agent name for screenshot directory
        adw_id=adw_id,
    )

    # Execute test
    response = execute_template(request)

    if not response.success:
        logger.error(f"Error running E2E test {test_name}: {response.output}")
        return E2ETestResult(
            test_name=test_name,
            status="failed",
            test_path=test_file,
            error=f"Test execution error: {response.output}",
        )

    # Parse the response
    try:
        # Parse JSON from response
        result_data = parse_json(response.output, dict)

        # Create E2ETestResult
        e2e_result = E2ETestResult(
            test_name=result_data.get("test_name", test_name),
            status=result_data.get("status", "failed"),
            test_path=test_file,
            screenshots=result_data.get("screenshots", []),
            error=result_data.get("error"),
        )

        # Report complete and show payload
        status_emoji = "✅" if e2e_result.passed else "❌"
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"{status_emoji} E2E test completed: {test_name}\n```json\n{e2e_result.model_dump_json(indent=2)}\n```",
            ),
        )

        return e2e_result
    except Exception as e:
        logger.error(f"Error parsing E2E test result for {test_name}: {e}")
        e2e_result = E2ETestResult(
            test_name=test_name,
            status="failed",
            test_path=test_file,
            error=f"Result parsing error: {str(e)}",
        )

        # Report complete and show payload
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"❌ E2E test completed: {test_name}\n```json\n{e2e_result.model_dump_json(indent=2)}\n```",
            ),
        )

        return e2e_result


def format_e2e_test_results_comment(
    results: List[E2ETestResult], passed_count: int, failed_count: int
) -> str:
    """Format E2E test results for GitHub issue comment."""
    if not results:
        return "❌ No E2E test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed E2E Tests")
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
        comment_parts.append("## ✅ Passed E2E Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            if test.screenshots:
                comment_parts.append(f"Screenshots: {len(test.screenshots)} captured")
            comment_parts.append("")

    # Remove trailing empty line
    if comment_parts and comment_parts[-1] == "":
        comment_parts.pop()

    return "\n".join(comment_parts)


def resolve_failed_e2e_tests(
    failed_tests: List[E2ETestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
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

        # Create template request
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_e2e_test",
            args=[test_payload],
            adw_id=adw_id,
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

        # Run E2E tests
        results = run_e2e_tests(adw_id, issue_number, logger, attempt)

        if not results:
            logger.warning("No E2E test results to process")
            break

        # Count passes and failures
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

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
            failed_tests, adw_id, issue_number, logger, iteration=attempt
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
# Test Ensurance System - Autonomous Test Creation and Validation
# ====================================================================


def extract_test_requirements_with_ai(
    plan_file: str, adw_id: str, logger: logging.Logger
) -> List[dict]:
    """
    Extract test requirements from plan file using AI.
    Returns list of test requirements.
    """
    logger.info(f"Extracting test requirements from {plan_file}")

    request = AgentTemplateRequest(
        agent_name="test_requirements_extractor",
        slash_command="/extract_test_requirements",
        args=[plan_file],
        adw_id=adw_id,
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"Failed to extract test requirements: {response.output}")
        return []

    try:
        # Parse JSON response
        requirements = parse_json(response.output, list)
        return requirements if requirements else []
    except Exception as e:
        logger.error(f"Error parsing test requirements: {e}")
        return []


def categorize_tests_fast(requirements: List[dict], logger: logging.Logger) -> dict:
    """
    Fast Python categorization of test files.
    Returns: {missing: [], obviously_broken: [], needs_validation: []}
    """
    import re

    result = {"missing": [], "obviously_broken": [], "needs_validation": []}

    for req in requirements:
        test_file = req.get("test_file_path")
        if not test_file:
            continue

        # Check 1: File exists?
        if not os.path.exists(test_file):
            logger.debug(f"  ✗ {test_file} - missing")
            result["missing"].append(req)
            continue

        # Check 2: Obviously broken?
        try:
            with open(test_file, "r") as f:
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
                # Quick analysis for AI
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
    tests_to_validate: List[dict], adw_id: str, logger: logging.Logger
) -> List[dict]:
    """
    Validate existing tests against requirements using AI (batched).
    Returns list of validation results.
    """
    if not tests_to_validate:
        return []

    logger.info(f"Validating {len(tests_to_validate)} test files with AI")

    # Build batch payload
    batch_payload = {"tests_to_validate": tests_to_validate}

    request = AgentTemplateRequest(
        agent_name="test_batch_validator",
        slash_command="/validate_test_batch",
        args=[json.dumps(batch_payload, indent=2)],
        adw_id=adw_id,
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"Failed to validate tests: {response.output}")
        return []

    try:
        # Parse JSON response
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

    # Missing files -> create
    actions["create"].extend(categorized.get("missing", []))

    # Obviously broken -> replace
    actions["replace"].extend(categorized.get("obviously_broken", []))

    # Validation results -> categorize based on recommendation
    for result in validation_results:
        recommendation = result.get("recommendation", "complete")
        test_file = result.get("test_file_path")

        # Find the original requirement
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

        # Add validation results to the requirement
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
    action_type: str, req: dict, adw_id: str, logger: logging.Logger
) -> Tuple[bool, str]:
    """
    Create or augment a test file using AI.
    Returns (success, test_file_path).
    """
    test_file = req.get("test_file_path")
    logger.info(f"{action_type.capitalize()}ing test: {test_file}")

    if action_type == "create":
        # Build context for creation
        context = {
            "test_file_path": test_file,
            "source_file_path": req.get("source_file_path", ""),
            "description": req.get("description", ""),
            "test_scenarios": req.get("test_scenarios", []),
            "relevant_edge_cases": req.get("relevant_edge_cases", []),
            "testing_framework": "pytest",  # Auto-detect or configurable
        }

        # Read source code if path exists
        source_file = req.get("source_file_path")
        if source_file and os.path.exists(source_file):
            try:
                with open(source_file, "r") as f:
                    context["source_code"] = f.read()
            except Exception as e:
                logger.warning(f"Could not read source file {source_file}: {e}")
                context["source_code"] = ""

        # Find example test for pattern
        example_test = find_example_test(logger)
        if example_test:
            context["example_test_code"] = example_test

        request = AgentTemplateRequest(
            agent_name=f"test_creator_{adw_id[:8]}",
            slash_command="/create_test",
            args=[json.dumps(context, indent=2)],
            adw_id=adw_id,
        )

    else:  # augment
        # Build context for augmentation
        validation = req.get("validation_result", {})
        coverage = validation.get("coverage_analysis", {})

        context = {
            "test_file_path": test_file,
            "existing_test_code": req.get("content", ""),
            "missing_scenarios": coverage.get("missing_scenarios", []),
            "edge_cases": req.get("relevant_edge_cases", []),
            "issues_to_fix": validation.get("issues", []),
        }

        # Read source code if available
        source_file = req.get("source_file_path")
        if source_file and os.path.exists(source_file):
            try:
                with open(source_file, "r") as f:
                    context["source_code"] = f.read()
            except Exception as e:
                logger.warning(f"Could not read source file {source_file}: {e}")
                context["source_code"] = ""

        request = AgentTemplateRequest(
            agent_name=f"test_augmentor_{adw_id[:8]}",
            slash_command="/augment_test",
            args=[json.dumps(context, indent=2)],
            adw_id=adw_id,
        )

    response = execute_template(request)

    if response.success:
        return True, test_file
    else:
        logger.error(f"Failed to {action_type} test {test_file}: {response.output}")
        return False, test_file


def find_example_test(logger: logging.Logger) -> Optional[str]:
    """Find an example test file to use as a pattern."""
    # Look for common test files
    example_paths = [
        "app/server/tests/test_health.py",
        "app/server/tests/test_api.py",
    ]

    import glob

    # Also glob for any test file
    test_files = glob.glob("app/server/tests/test_*.py")

    # Try specific examples first
    for path in example_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return f.read()
            except Exception as e:
                logger.debug(f"Could not read example {path}: {e}")

    # Try any test file
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
    actions: dict, adw_id: str, logger: logging.Logger, max_workers: int = 5
) -> dict:
    """
    Execute create/augment actions in parallel.
    Returns: {created: [], augmented: [], failed: []}
    """
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

    logger.info(f"Executing {len(tasks)} test creation/augmentation tasks")

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
    execution_results: dict, adw_id: str, logger: logging.Logger, max_fix_attempts: int = 2
) -> dict:
    """
    Run pytest on created tests and attempt to fix failures.
    Returns: {created_and_passing: [], augmented_and_passing: [], created_but_failing: []}
    """
    validated = {
        "created_and_passing": [],
        "augmented_and_passing": [],
        "created_but_failing": [],
    }

    all_tests = execution_results.get("created", []) + execution_results.get(
        "augmented", []
    )

    for test_file in all_tests:
        action_type = (
            "created" if test_file in execution_results.get("created", []) else "augmented"
        )

        logger.info(f"Validating {test_file}...")

        # Determine working directory and relative path
        if "app/server" in test_file:
            cwd = "app/server"
            relative_path = test_file.replace("app/server/", "")
        elif "app/client" in test_file:
            cwd = "app/client"
            relative_path = test_file.replace("app/client/", "")
        else:
            # Fallback to current directory
            cwd = "."
            relative_path = test_file

        # Run pytest on just this file
        result = subprocess.run(
            ["uv", "run", "pytest", relative_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=cwd,
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
    max_attempts: int,
) -> bool:
    """Attempt to fix failing test with AI."""

    for attempt in range(1, max_attempts + 1):
        logger.info(f"Fix attempt {attempt}/{max_attempts} for {test_file}...")

        # Read current test code
        try:
            with open(test_file, "r") as f:
                test_code = f.read()
        except Exception as e:
            logger.error(f"Could not read test file {test_file}: {e}")
            return False

        # Call fix agent
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
        )

        response = execute_template(request)

        if not response.success:
            logger.error(f"Fix attempt {attempt} failed: {response.output}")
            continue

        # Determine working directory and relative path
        if "app/server" in test_file:
            cwd = "app/server"
            relative_path = test_file.replace("app/server/", "")
        elif "app/client" in test_file:
            cwd = "app/client"
            relative_path = test_file.replace("app/client/", "")
        else:
            cwd = "."
            relative_path = test_file

        # Re-run pytest
        result = subprocess.run(
            ["uv", "run", "pytest", relative_path, "-v"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode == 0:
            logger.info(f"Fix successful on attempt {attempt}")
            return True

        # Update error for next attempt
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
    plan_file: str, adw_id: str, issue_number: str, logger: logging.Logger
) -> TestEnsuranceReport:
    """
    Ensure all planned tests exist and are complete.
    Returns report of actions taken.
    """
    logger.info("=== Test Ensurance Phase ===")

    # STEP 1: Extract requirements (AI - 1 call)
    logger.info("Step 1: Extracting test requirements from plan...")
    requirements = extract_test_requirements_with_ai(plan_file, adw_id, logger)
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
        execution_results = execute_test_actions_parallel(actions, adw_id, logger)
    else:
        logger.info("Step 5: No test creation needed - all tests complete")
        execution_results = {"created": [], "augmented": [], "failed": []}

    # STEP 6: Validate created tests
    if execution_results["created"] or execution_results["augmented"]:
        logger.info("Step 6: Validating created tests...")
        validated = validate_and_fix_created_tests(execution_results, adw_id, logger)
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

    # Parse arguments
    arg_issue_number, arg_adw_id, skip_e2e = parse_args(None)

    # Initialize state and issue number
    issue_number = arg_issue_number

    # Ensure we have an issue number
    if not issue_number:
        print("Error: No issue number provided", file=sys.stderr)
        sys.exit(1)

    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(arg_adw_id, "adw_test") if arg_adw_id else None
    adw_id = ensure_adw_id(issue_number, arg_adw_id, temp_logger)

    # Load the state that was created/found by ensure_adw_id
    state = ADWState.load(adw_id, temp_logger)

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_test")

    # Rich console: Workflow start
    log_workflow_start("adw_test", adw_id, int(issue_number))
    logger.info(f"ADW Test starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment (now with logger)
    check_env_vars(logger)

    # Get repo information from git remote
    try:
        github_repo_url: str = get_repo_url()
        repo_path: str = extract_repo_path(github_repo_url)
    except ValueError as e:
        log_error("Error getting repository URL", e)
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # We'll fetch issue details later only if needed
    issue = None
    issue_class = state.get("issue_class")

    # Rich console: Branch handling section
    ADWLogger.separator("Branch Handling")

    # Handle branch - either use existing or create new test branch
    branch_name = state.get("branch_name")
    if branch_name:
        # Try to checkout existing branch
        result = subprocess.run(
            ["git", "checkout", branch_name], capture_output=True, text=True
        )
        if result.returncode != 0:
            log_error("Failed to checkout branch", Exception(result.stderr))
            logger.error(f"Failed to checkout branch {branch_name}: {result.stderr}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"❌ Failed to checkout branch {branch_name}"
                ),
            )
            sys.exit(1)
        ADWLogger.git_operation("Checked Out", branch_name)
        logger.info(f"Checked out existing branch: {branch_name}")
    else:
        # No branch in state - create a test-specific branch
        logger.info("No branch in state, creating test branch")

        # Generate simple test branch name without classification
        branch_name = f"test-issue-{issue_number}-adw-{adw_id}"
        logger.info(f"Generated test branch name: {branch_name}")

        # Create the branch
        from adw_modules.git_ops import create_branch

        success, error = create_branch(branch_name)
        if not success:
            log_error("Error creating branch", Exception(error))
            logger.error(f"Error creating branch: {error}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"❌ Error creating branch: {error}"
                ),
            )
            sys.exit(1)

        state.update(branch_name=branch_name)
        state.save("adw_test")
        ADWLogger.git_operation("Branch Created", branch_name)
        ADWLogger.state_update(adw_id, "branch_name", branch_name)
        logger.info(f"Created and checked out new test branch: {branch_name}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"✅ Created test branch: {branch_name}"
            ),
        )

    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Starting test suite")
    )

    # NEW: Test Ensurance Phase (autonomous test creation)
    spec_file = state.get("plan_file")
    if spec_file and os.path.exists(spec_file):
        ADWLogger.separator("Test Ensurance")
        logger.info("\n=== Test Ensurance Phase ===")

        report = ensure_tests_exist_and_complete(
            plan_file=spec_file, adw_id=adw_id, issue_number=issue_number, logger=logger
        )

        # Report results to GitHub
        if report.created > 0 or report.augmented > 0:
            make_issue_comment(
                issue_number, format_test_ensurance_report(report, adw_id)
            )

            # Commit the new/updated tests
            logger.info("Committing created/augmented tests...")
            commit_files = []
            # Collect all test files that were created or augmented
            # Note: This is a simplified approach - in production we'd track exact files
            import glob

            test_files = glob.glob("app/server/tests/test_*.py")
            for tf in test_files:
                # Check if file was recently modified (within last minute)
                if os.path.exists(tf):
                    mtime = os.path.getmtime(tf)
                    import time

                    if time.time() - mtime < 60:  # Modified in last 60 seconds
                        commit_files.append(tf)

            if commit_files:
                commit_msg = f"test_creator: feature: add/update unit tests\n\n"
                commit_msg += f"- Created: {report.created} test files\n"
                commit_msg += f"- Augmented: {report.augmented} test files\n"
                commit_msg += f"- All created tests passing: {report.all_passing}\n\n"
                commit_msg += (
                    "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
                )
                commit_msg += "Co-Authored-By: Claude <noreply@anthropic.com>"

                success, error = commit_changes(commit_msg)
                if success:
                    logger.info("Test files committed successfully")
                else:
                    logger.warning(f"Failed to commit test files: {error}")
    else:
        logger.info("No plan file found in state, skipping test ensurance phase")

    # Rich console: Test execution section
    ADWLogger.separator("Unit Test Execution")

    # Run tests with automatic resolution and retry
    logger.info("\n=== Running test suite ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "✅ Running application tests..."),
    )

    # Run tests with resolution and retry logic
    results, passed_count, failed_count, test_response = run_tests_with_resolution(
        adw_id, issue_number, logger
    )

    # Format and post final results
    results_comment = format_test_results_comment(results, passed_count, failed_count)
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, AGENT_TESTER, f"📊 Final test results:\n{results_comment}"
        ),
    )

    # Log summary
    logger.info(f"Final test results: {passed_count} passed, {failed_count} failed")

    # If unit tests failed or skip_e2e flag is set, skip E2E tests
    if failed_count > 0:
        logger.warning("Skipping E2E tests due to unit test failures")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping E2E tests due to unit test failures"
            ),
        )
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    elif skip_e2e:
        logger.info("Skipping E2E tests as requested")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping E2E tests as requested via --skip-e2e flag"
            ),
        )
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    else:
        # Rich console: E2E test execution section
        ADWLogger.separator("E2E Test Execution")

        # Run E2E tests since unit tests passed
        logger.info("\n=== Running E2E test suite ===")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_E2E_TESTER, "✅ Starting E2E tests..."),
        )

        # Run E2E tests with resolution and retry logic
        e2e_results, e2e_passed_count, e2e_failed_count = run_e2e_tests_with_resolution(
            adw_id, issue_number, logger
        )

        # Format and post E2E results
        if e2e_results:
            e2e_results_comment = format_e2e_test_results_comment(
                e2e_results, e2e_passed_count, e2e_failed_count
            )
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"📊 Final E2E test results:\n{e2e_results_comment}",
                ),
            )

            logger.info(
                f"Final E2E test results: {e2e_passed_count} passed, {e2e_failed_count} failed"
            )

    # Rich console: Commit section
    ADWLogger.separator("Test Results Commit")

    # Commit the test results (whether tests passed or failed)
    logger.info("\n=== Committing test results ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "✅ Committing test results"),
    )

    # Fetch issue details if we haven't already
    if not issue:
        issue = fetch_issue(issue_number, repo_path)

    # Get issue classification if we need it for commit
    if not issue_class:
        issue_class, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.warning(
                f"Error classifying issue: {error}, defaulting to /chore for test commit"
            )
            issue_class = "/chore"
        state.update(issue_class=issue_class)
        state.save("adw_test")

    commit_msg, error = create_commit(AGENT_TESTER, issue, issue_class, adw_id, logger)

    if error:
        log_error("Error committing test results", Exception(error))
        logger.error(f"Error committing test results: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_TESTER, f"❌ Error committing test results: {error}"
            ),
        )
        # Don't exit on commit error, continue to report final status
    else:
        ADWLogger.git_operation("Committed", commit_msg[:60] + "..." if len(commit_msg) > 60 else commit_msg)
        logger.info(f"Test results committed: {commit_msg}")

    # Log comprehensive test results to the issue
    log_test_results(state, results, e2e_results, logger)

    # Finalize git operations (push and create/update PR)
    logger.info("\n=== Finalizing git operations ===")
    finalize_git_operations(state, logger)

    # Update state with test results
    # Note: test_results is not part of core state, but save anyway to track completion
    state.save("adw_test")

    # Output state for chaining
    state.to_stdout()

    # Rich console: Workflow complete
    total_failures = failed_count + e2e_failed_count
    log_workflow_complete("adw_test", adw_id, success=(total_failures == 0))

    # Exit with appropriate code
    if total_failures > 0:
        logger.info(f"Test suite completed with failures for issue #{issue_number}")
        failure_msg = f"❌ Test suite completed with failures:\n"
        if failed_count > 0:
            failure_msg += f"- Unit tests: {failed_count} failures\n"
        if e2e_failed_count > 0:
            failure_msg += f"- E2E tests: {e2e_failed_count} failures"
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", failure_msg),
        )
        sys.exit(1)
    else:
        logger.info(f"Test suite completed successfully for issue #{issue_number}")
        success_msg = f"✅ All tests passed successfully!\n"
        success_msg += f"- Unit tests: {passed_count} passed\n"
        if e2e_results:
            success_msg += f"- E2E tests: {e2e_passed_count} passed"
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", success_msg),
        )


if __name__ == "__main__":
    main()
