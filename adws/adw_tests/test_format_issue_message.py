#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""
Unit tests for format_issue_message() function.

Tests the ADW bot identifier formatting to ensure all issue comments
are properly prefixed with [ADW-BOT] to prevent webhook classification loops.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.utils import format_issue_message
from adw_modules.github import ADW_BOT_IDENTIFIER


def test_basic_message_format():
    """Test basic message formatting with adw_id and agent_name."""
    adw_id = "3e81e604"
    agent_name = "ops"
    message = "Test message"

    result = format_issue_message(adw_id, agent_name, message)

    # Should contain bot identifier
    assert ADW_BOT_IDENTIFIER in result, f"Missing bot identifier in: {result}"

    # Should contain adw_id_agent_name prefix
    assert f"{adw_id}_{agent_name}:" in result, f"Missing adw_id_agent_name in: {result}"

    # Should contain the message
    assert message in result, f"Missing message in: {result}"

    # Should follow exact format
    expected = f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"
    assert result == expected, f"Expected: {expected}\nGot: {result}"

    print(f"✅ test_basic_message_format passed")
    print(f"   Result: {result}")


def test_with_session_id():
    """Test message formatting with optional session_id."""
    adw_id = "3e81e604"
    agent_name = "planner"
    session_id = "session-123"
    message = "Planning started"

    result = format_issue_message(adw_id, agent_name, message, session_id)

    # Should contain bot identifier
    assert ADW_BOT_IDENTIFIER in result, f"Missing bot identifier in: {result}"

    # Should contain adw_id_agent_name_session_id prefix
    assert f"{adw_id}_{agent_name}_{session_id}:" in result, \
        f"Missing adw_id_agent_name_session_id in: {result}"

    # Should contain the message
    assert message in result, f"Missing message in: {result}"

    # Should follow exact format with session
    expected = f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    assert result == expected, f"Expected: {expected}\nGot: {result}"

    print(f"✅ test_with_session_id passed")
    print(f"   Result: {result}")


def test_multiline_message():
    """Test formatting with multiline messages."""
    adw_id = "3e81e604"
    agent_name = "ops"
    message = "🚀 Starting workflow\n\nStep 1: Plan\nStep 2: Build"

    result = format_issue_message(adw_id, agent_name, message)

    # Should contain bot identifier
    assert ADW_BOT_IDENTIFIER in result, f"Missing bot identifier in: {result}"

    # Should preserve all newlines and content
    assert "Step 1: Plan" in result
    assert "Step 2: Build" in result
    assert "🚀 Starting workflow" in result

    print(f"✅ test_multiline_message passed")
    print(f"   Result: {result[:100]}...")


def test_json_message():
    """Test formatting with JSON content in message."""
    adw_id = "3e81e604"
    agent_name = "ops"
    message = '{"status": "complete", "adw_id": "3e81e604"}'

    result = format_issue_message(adw_id, agent_name, message)

    # Should contain bot identifier BEFORE the JSON
    assert result.startswith(ADW_BOT_IDENTIFIER), \
        f"Bot identifier should be at start: {result}"

    # Should preserve JSON in message
    assert '"status": "complete"' in result
    assert '"adw_id": "3e81e604"' in result

    print(f"✅ test_json_message passed")
    print(f"   Result: {result}")


def test_bot_identifier_value():
    """Verify the bot identifier constant has correct value."""
    # This is the critical identifier that prevents webhook loops
    assert ADW_BOT_IDENTIFIER == "[ADW-BOT]", \
        f"Bot identifier should be [ADW-BOT], got: {ADW_BOT_IDENTIFIER}"

    print(f"✅ test_bot_identifier_value passed")
    print(f"   Identifier: {ADW_BOT_IDENTIFIER}")


def test_various_agent_names():
    """Test with different agent names used in the system."""
    adw_id = "3e81e604"
    agent_names = [
        "ops",
        "planner",
        "implementor",
        "tester",
        "reviewer",
        "documenter",
        "shipper",
        "patch_planner",
        "patch_implementor",
    ]

    for agent_name in agent_names:
        message = f"Test from {agent_name}"
        result = format_issue_message(adw_id, agent_name, message)

        # All should have bot identifier
        assert ADW_BOT_IDENTIFIER in result

        # All should have correct prefix
        assert f"{adw_id}_{agent_name}:" in result

        print(f"   ✓ Agent '{agent_name}': {result}")

    print(f"✅ test_various_agent_names passed")


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "="*70)
    print("Running format_issue_message() Unit Tests")
    print("="*70 + "\n")

    tests = [
        test_bot_identifier_value,
        test_basic_message_format,
        test_with_session_id,
        test_multiline_message,
        test_json_message,
        test_various_agent_names,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print()
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}\n")
            failed += 1

    print("="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
