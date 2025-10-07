"""Claude Code agent module for executing prompts programmatically."""

import subprocess
import sys
import os
import json
import re
import logging
import time
from typing import Optional, List, Dict, Any, Tuple, Final
from dotenv import load_dotenv
from .data_types import (
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    ClaudeCodeResultMessage,
    SlashCommand,
    ModelSet,
    RetryCode,
)

# Load environment variables
load_dotenv()

# Get Claude Code CLI path from environment
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")

# Model selection mapping for slash commands
# Maps each command to its model configuration for base and heavy model sets
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
    # Test ensurance and analysis commands
    "/extract_test_requirements": {"base": "sonnet", "heavy": "sonnet"},
    "/validate_test_batch": {"base": "sonnet", "heavy": "sonnet"},
    "/create_test": {"base": "sonnet", "heavy": "opus"},
    "/augment_test": {"base": "sonnet", "heavy": "opus"},
    "/fix_test": {"base": "sonnet", "heavy": "opus"},
    "/test_doctor": {"base": "sonnet", "heavy": "sonnet"},
}


def get_model_for_slash_command(
    request: AgentTemplateRequest, default: str = "sonnet"
) -> str:
    """Get the appropriate model for a template request based on ADW state and slash command.

    This function loads the ADW state to determine the model set (base or heavy)
    and returns the appropriate model for the slash command.

    Args:
        request: The template request containing the slash command and adw_id
        default: Default model if not found in mapping

    Returns:
        Model name to use (e.g., "sonnet" or "opus")
    """
    # Import here to avoid circular imports
    from .state import ADWState

    # Load state to get model_set
    model_set: ModelSet = "base"  # Default model set
    state = ADWState.load(request.adw_id)
    if state:
        model_set = state.get("model_set", "base")

    # Get the model configuration for the command
    command_config = SLASH_COMMAND_MODEL_MAP.get(request.slash_command)

    if command_config:
        # Get the model for the specified model set, defaulting to base if not found
        return command_config.get(model_set, command_config.get("base", default))

    return default


def _legacy_get_model_for_slash_command(slash_command: str, default: str = "sonnet") -> str:
    """Get the recommended model for a slash command.

    Args:
        slash_command: The slash command to look up
        default: Default model if not found in mapping

    Returns:
        Model name to use
    """
    return SLASH_COMMAND_MODEL_MAP.get(slash_command, default)


def check_claude_installed() -> Optional[str]:
    """Check if Claude Code CLI is installed. Return error message if not."""
    try:
        result = subprocess.run(
            [CLAUDE_PATH, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return (
                f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
            )
    except FileNotFoundError:
        return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    return None


def parse_jsonl_output(
    output_file: str,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse JSONL output file and return all messages and the result message.

    Returns:
        Tuple of (all_messages, result_message) where result_message is None if not found
    """
    messages = []
    try:
        with open(output_file, "r") as f:
            # Read and parse each line individually to handle partial failures
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError as e:
                    # Skip malformed lines but log them for debugging
                    # This is common with very large output from Claude Code
                    print(f"Skipping malformed JSON at line {line_num} in {output_file}: {e}", file=sys.stderr)
                    continue

            # Find the result message (should be the last one)
            result_message = None
            for message in reversed(messages):
                if message.get("type") == "result":
                    result_message = message
                    break

            return messages, result_message
    except Exception as e:
        print(f"Error parsing JSONL file {output_file}: {e}", file=sys.stderr)
        return messages, None  # Return what we parsed so far


def convert_jsonl_to_json(jsonl_file: str) -> str:
    """Convert JSONL file to JSON array file.

    Creates a .json file with the same name as the .jsonl file,
    containing all messages as a JSON array.

    Returns:
        Path to the created JSON file
    """
    # Create JSON filename by replacing .jsonl with .json
    json_file = jsonl_file.replace(".jsonl", ".json")

    # Parse the JSONL file
    messages, _ = parse_jsonl_output(jsonl_file)

    # Write as JSON array
    with open(json_file, "w") as f:
        json.dump(messages, f, indent=2)

    print(f"Created JSON file: {json_file}")
    return json_file


def get_claude_env() -> Dict[str, str]:
    """Get only the required environment variables for Claude Code execution.

    This is a wrapper around get_safe_subprocess_env() from utils.py for
    backward compatibility. New code should use get_safe_subprocess_env() directly.

    Returns a dictionary containing only the necessary environment variables
    based on .env.sample configuration.
    """
    # Import here to avoid circular imports
    from .utils import get_safe_subprocess_env

    # Use the shared function
    return get_safe_subprocess_env()


def save_prompt(prompt: str, adw_id: str, agent_name: str = "ops") -> None:
    """Save a prompt to the appropriate logging directory."""
    # Extract slash command from prompt
    match = re.match(r"^(/\w+)", prompt)
    if not match:
        return

    slash_command = match.group(1)
    # Remove leading slash for filename
    command_name = slash_command[1:]

    # Create directory structure at project root (parent of adws)
    # __file__ is in adws/adw_modules/, so we need to go up 3 levels to get to project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompt_dir = os.path.join(project_root, "agents", adw_id, agent_name, "prompts")
    os.makedirs(prompt_dir, exist_ok=True)

    # Save prompt to file
    prompt_file = os.path.join(prompt_dir, f"{command_name}.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)

    print(f"Saved prompt to: {prompt_file}")


def prompt_claude_code_with_retry(
    request: AgentPromptRequest,
    max_retries: int = 3,
    retry_delays: List[int] = None,
) -> AgentPromptResponse:
    """Execute Claude Code with retry logic for certain error types.

    Args:
        request: The prompt request configuration
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delays: List of delays in seconds between retries (default: [1, 3, 5])

    Returns:
        AgentPromptResponse with output and success status
    """
    if retry_delays is None:
        retry_delays = [1, 3, 5]

    # Ensure we have enough delays for max_retries
    while len(retry_delays) < max_retries:
        retry_delays.append(retry_delays[-1] + 2)  # Add incrementing delays

    last_response = None

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if attempt > 0:
            # This is a retry
            delay = retry_delays[attempt - 1]
            time.sleep(delay)

        response = prompt_claude_code(request)
        last_response = response

        # Success - return immediately
        if response.success:
            return response

        # For now, we don't have retry_code in AgentPromptResponse yet
        # So we'll just retry on failure up to max_retries
        if attempt < max_retries:
            continue
        else:
            return response

    # Should not reach here, but return last response just in case
    return last_response


def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute Claude Code with the given prompt configuration."""

    # Check if Claude Code CLI is installed
    error_msg = check_claude_installed()
    if error_msg:
        return AgentPromptResponse(output=error_msg, success=False, session_id=None)

    # Save prompt before execution
    save_prompt(request.prompt, request.adw_id, request.agent_name)

    # Create output directory if needed
    output_dir = os.path.dirname(request.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Build command - always use stream-json format and verbose
    cmd = [CLAUDE_PATH, "-p", request.prompt]
    cmd.extend(["--model", request.model])
    cmd.extend(["--output-format", "stream-json"])
    cmd.append("--verbose")

    # Add dangerous skip permissions flag if enabled
    if request.dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    # Set up environment with only required variables
    env = get_claude_env()

    try:
        # Execute Claude Code and pipe output to file
        with open(request.output_file, "w") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=request.working_dir,  # Support working directory
            )

        if result.returncode == 0:
            print(f"Output saved to: {request.output_file}")

            # Parse the JSONL file
            messages, result_message = parse_jsonl_output(request.output_file)

            # Convert JSONL to JSON array file
            json_file = convert_jsonl_to_json(request.output_file)

            if result_message:
                # Extract session_id from result message
                session_id = result_message.get("session_id")

                # Check if there was an error in the result
                is_error = result_message.get("is_error", False)
                subtype = result_message.get("subtype", "")

                # Handle error_during_execution case where there's no result field
                if subtype == "error_during_execution":
                    error_msg = "Error during execution: Agent encountered an error and did not return a result"
                    return AgentPromptResponse(
                        output=error_msg, success=False, session_id=session_id
                    )

                result_text = result_message.get("result", "")

                return AgentPromptResponse(
                    output=result_text, success=not is_error, session_id=session_id
                )
            else:
                # No result message found, return raw output
                with open(request.output_file, "r") as f:
                    raw_output = f.read()
                return AgentPromptResponse(
                    output=raw_output, success=True, session_id=None
                )
        else:
            error_msg = f"Claude Code error: {result.stderr}"
            print(error_msg, file=sys.stderr)
            return AgentPromptResponse(output=error_msg, success=False, session_id=None)

    except subprocess.TimeoutExpired:
        error_msg = "Error: Claude Code command timed out after 5 minutes"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False, session_id=None)
    except Exception as e:
        error_msg = f"Error executing Claude Code: {e}"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False, session_id=None)


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a Claude Code template with slash command and arguments.

    This function automatically selects the appropriate model based on:
    1. The slash command being executed
    2. The model_set stored in the ADW state (base or heavy)

    Example:
        request = AgentTemplateRequest(
            agent_name="planner",
            slash_command="/implement",
            args=["plan.md"],
            adw_id="abc12345"
        )
        # If state has model_set="heavy", this will use "opus"
        # If state has model_set="base" or missing, this will use "sonnet"
        response = execute_template(request)
    """
    # Get the appropriate model for this request
    mapped_model = get_model_for_slash_command(request)
    request = request.model_copy(update={"model": mapped_model})

    # Construct prompt from slash command and args
    prompt = f"{request.slash_command} {' '.join(request.args)}"

    # Create output directory with adw_id at project root
    # __file__ is in adws/adw_modules/, so we need to go up 3 levels to get to project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    output_dir = os.path.join(
        project_root, "agents", request.adw_id, request.agent_name
    )
    os.makedirs(output_dir, exist_ok=True)

    # Build output file path
    output_file = os.path.join(output_dir, "raw_output.jsonl")

    # Create prompt request with specific parameters
    prompt_request = AgentPromptRequest(
        prompt=prompt,
        adw_id=request.adw_id,
        agent_name=request.agent_name,
        model=request.model,
        dangerously_skip_permissions=True,
        output_file=output_file,
        working_dir=request.working_dir,  # Pass through working_dir
    )

    # Execute with retry logic and return response
    return prompt_claude_code_with_retry(prompt_request)
