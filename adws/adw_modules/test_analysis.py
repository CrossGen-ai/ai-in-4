"""
Shared test analysis logic for both standard and ISO workflows.

This module provides test failure diagnosis and pattern learning capabilities
that can be used by both adw_test.py and adw_test_iso.py.
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path
from .agent import execute_template
from .data_types import AgentTemplateRequest, AgentPromptResponse
from .test_doctor import (
    update_pattern_tracker,
    update_knowledge_base,
    apply_fix,
)


def analyze_and_fix_test_failures(
    test_output: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,  # None = standard, path = ISO
    auto_fix: bool = True,
) -> Dict:
    """
    Unified test failure analysis for both workflows.

    Args:
        test_output: Pytest output from test run
        adw_id: Current ADW ID
        logger: Logger instance
        working_dir: None for standard mode, worktree path for ISO mode
        auto_fix: Whether to automatically apply fixes (default True)

    Returns:
        Analysis metrics dict with:
        - total_failures: int
        - known_patterns: int
        - new_patterns: int
        - fixes_applied: int
        - diagnosis: dict (full diagnosis from test_doctor)
    """
    logger.info("Analyzing test failures with test_doctor...")

    # Run test_doctor diagnosis via slash command
    diagnosis_result = run_test_doctor(
        test_output=test_output,
        adw_id=adw_id,
        logger=logger,
        working_dir=working_dir,
    )

    # Parse diagnosis
    diagnosis = parse_diagnosis_output(diagnosis_result.output, logger)

    # Track metrics
    metrics = {
        "total_failures": diagnosis.get("total_failures", 0),
        "known_patterns": diagnosis.get("known_patterns", 0),
        "new_patterns": diagnosis.get("new_patterns", 0),
        "fixes_applied": 0,
        "diagnosis": diagnosis,
    }

    # Apply suggested fixes if enabled and high confidence
    if auto_fix:
        for failure in diagnosis.get("failures", []):
            if failure.get("confidence") == "high" and failure.get("fix"):
                try:
                    # Apply fix with working_dir awareness
                    apply_fix(failure["fix"], working_dir=working_dir)
                    metrics["fixes_applied"] += 1
                    logger.info(
                        f"Auto-applied fix for: {failure.get('test_name', 'unknown')}"
                    )
                except Exception as e:
                    logger.warning(f"Could not auto-apply fix: {e}")

    # Update knowledge base if new patterns found
    if metrics["new_patterns"] > 0:
        new_patterns_data = diagnosis.get("new_patterns_data", [])
        if new_patterns_data:
            update_knowledge_base(new_patterns_data, logger)
            logger.info(f"Documented {len(new_patterns_data)} new patterns in KB")

    # Update pattern frequency tracker
    pattern_matches = diagnosis.get("pattern_matches", [])
    if pattern_matches:
        update_pattern_tracker(pattern_matches)
        logger.info(f"Updated frequency tracker with {len(pattern_matches)} patterns")

    return metrics


def run_test_doctor(
    test_output: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """
    Run /test_doctor slash command to diagnose test failures.

    Args:
        test_output: Pytest output
        adw_id: Current ADW ID
        logger: Logger instance
        working_dir: Optional working directory for ISO mode

    Returns:
        AgentPromptResponse with diagnosis
    """
    # Create test_doctor request with test output as argument
    test_output_arg = f"""Analyze these test failures and provide diagnosis:

```
{test_output}
```

Review the testing knowledge base at app_docs/testing/ and:
1. Identify failure patterns
2. Match against known patterns
3. Suggest fixes with high/medium/low confidence
4. Extract any new patterns (confidence < 50%)

Return diagnosis in structured format."""

    request = AgentTemplateRequest(
        agent_name="test_doctor",
        slash_command="/test_doctor",
        args=[test_output_arg],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    # Execute with working_dir if provided (ISO mode)
    result = execute_template(request)

    return result


def parse_diagnosis_output(output: str, logger: logging.Logger) -> Dict:
    """
    Parse test_doctor output into structured diagnosis.

    Args:
        output: Raw output from test_doctor
        logger: Logger instance

    Returns:
        Structured diagnosis dict
    """
    # This is a simplified parser - in production, would use more robust parsing
    diagnosis = {
        "total_failures": 0,
        "known_patterns": 0,
        "new_patterns": 0,
        "failures": [],
        "pattern_matches": [],
        "new_patterns_data": [],
    }

    try:
        # Extract key metrics from output
        if "Total Failures:" in output:
            total_match = output.split("Total Failures:")[1].split("\n")[0].strip()
            diagnosis["total_failures"] = int(total_match.split()[0])

        if "Known Patterns:" in output:
            known_match = output.split("Known Patterns:")[1].split("\n")[0].strip()
            diagnosis["known_patterns"] = int(known_match.split()[0])

        if "New Patterns:" in output:
            new_match = output.split("New Patterns:")[1].split("\n")[0].strip()
            diagnosis["new_patterns"] = int(new_match.split()[0])

        # TODO: Parse individual failures, fixes, and patterns
        # This would require more sophisticated parsing of the markdown output

    except Exception as e:
        logger.warning(f"Could not fully parse diagnosis output: {e}")

    return diagnosis


def should_rerun_tests(metrics: Dict) -> bool:
    """
    Determine if tests should be re-run after fixes.

    Args:
        metrics: Analysis metrics from analyze_and_fix_test_failures

    Returns:
        True if tests should be re-run
    """
    return metrics["fixes_applied"] > 0
