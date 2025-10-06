# Rich Logging Implementation Guide

> How to add beautiful, structured logging to ADW workflows

## Overview

This guide shows how to integrate Rich console logging into the ADW system for better readability in terminals and GitHub Actions logs.

**Benefits**:
- ✅ Visual hierarchy with panels and tables
- ✅ Color-coded output by agent type
- ✅ Emoji-based quick scanning
- ✅ Better debugging experience
- ✅ Works in GitHub Actions

## Table of Contents

1. [Installation](#installation)
2. [Basic Integration](#basic-integration)
3. [Before & After Examples](#before--after-examples)
4. [Complete Workflow Integration](#complete-workflow-integration)
5. [GitHub Actions Output](#github-actions-output)

---

## Installation

### Step 1: Add Rich to Script Dependencies

For uv-based scripts, add `rich` to the dependencies header:

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///
```

### Step 2: Import the Logger

```python
from adw_modules.rich_logging import ADWLogger, log_workflow_start, log_workflow_complete, log_error
```

That's it! Rich will be automatically installed when the script runs.

---

## Basic Integration

### Import the Logger

```python
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_command,
    log_error,
)
```

### Use in Your Workflow

```python
def main():
    adw_id = "adw-12345"
    issue_number = 42

    # Log workflow start
    log_workflow_start("adw_plan", adw_id, issue_number)

    try:
        # Your workflow code here
        result = run_slash_command("/plan", adw_id, [str(issue_number)])

        # Log success
        log_workflow_complete("adw_plan", adw_id, success=True)

    except Exception as e:
        # Log error
        log_error(f"Workflow failed", e)
        log_workflow_complete("adw_plan", adw_id, success=False)
```

---

## Before & After Examples

### Example 1: Workflow Start

#### Before (Standard Logging)
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Starting adw_plan for issue #{issue_number} (ADW ID: {adw_id})")
```

**Output**:
```
INFO:__main__:Starting adw_plan for issue #42 (ADW ID: adw-12345)
```

#### After (Rich Logging)
```python
from adw_modules.rich_logging import log_workflow_start

log_workflow_start("adw_plan", adw_id, issue_number)
```

**Output**:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 Starting Workflow: adw_plan                                 ┃
┠────────────────────────────────────────────────────────────────┨
┃ ADW ID: adw-12345                                              ┃
┃ Issue: #42                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Example 2: Slash Command Execution

#### Before
```python
logger.info(f"Running {slash_command} with model {model}")
logger.info(f"Arguments: {args}")
```

**Output**:
```
INFO:__main__:Running /implement with model sonnet
INFO:__main__:Arguments: ['plan.md']
```

#### After
```python
ADWLogger.slash_command_start("/implement", ["plan.md"], adw_id, model="sonnet")
```

**Output**:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 Executing Slash Command                                     ┃
┠────────────────────────────────────────────────────────────────┨
┃ Command      /implement                                        ┃
┃ ADW ID       adw-12345                                         ┃
┃ Model        sonnet                                            ┃
┃ Args         plan.md                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Example 3: Tool Calls

#### Before
```python
logger.info(f"Writing to {file_path}")
```

**Output**:
```
INFO:__main__:Writing to agents/adw-12345/plan.md
```

#### After
```python
ADWLogger.tool_call("Write", file_path="agents/adw-12345/plan.md")
```

**Output**:
```
📝 Write: `agents/adw-12345/plan.md`
```

### Example 4: State Updates

#### Before
```python
logger.info(f"Updated state: plan_file = {plan_file}")
```

**Output**:
```
INFO:__main__:Updated state: plan_file = agents/adw-12345/plan.md
```

#### After
```python
ADWLogger.state_update(adw_id, "plan_file", plan_file)
```

**Output**:
```
ℹ️  State Update [adw-12345]: plan_file = agents/adw-12345/plan.md
```

### Example 5: Git Operations

#### Before
```python
logger.info(f"Created branch: {branch_name}")
```

**Output**:
```
INFO:__main__:Created branch: feature/42-add-dark-mode
```

#### After
```python
ADWLogger.git_operation("Branch Created", branch_name)
```

**Output**:
```
🔀 Git Branch Created: feature/42-add-dark-mode
```

### Example 6: Model Selection

#### Before
```python
logger.info(f"Using {model} model for {command}")
```

**Output**:
```
INFO:__main__:Using opus model for /implement
```

#### After
```python
ADWLogger.model_selection("/implement", "heavy", "opus")
```

**Output**:
```
🎯 Model Selection: /implement → heavy set → opus
```

### Example 7: Error Logging

#### Before
```python
logger.error(f"Command failed: {error}")
```

**Output**:
```
ERROR:__main__:Command failed: Connection timeout
```

#### After
```python
ADWLogger.error("Command failed", exception=error)
```

**Output**:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ❌ Error                                                        ┃
┠────────────────────────────────────────────────────────────────┨
┃ Error: Command failed                                          ┃
┃ Exception: Connection timeout                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Complete Workflow Integration

Here's a complete example of integrating Rich logging into an ADW workflow:

### File: `adws/adw_plan.py` (Updated)

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "rich"]
# ///

"""ADW Plan - AI Developer Workflow for agentic planning"""

import sys
from pathlib import Path
from adw_modules.agent import run_slash_command, get_model_for_slash_command
from adw_modules.state import ADWState
from adw_modules.github_utils import fetch_issue, create_branch
from adw_modules.rich_logging import (
    ADWLogger,
    log_workflow_start,
    log_workflow_complete,
    log_command,
    log_error,
)


def main():
    if len(sys.argv) < 2:
        log_error("Missing issue number argument")
        sys.exit(1)

    issue_number = int(sys.argv[1])
    adw_id = sys.argv[2] if len(sys.argv) > 2 else f"adw-{issue_number}"

    # Start workflow with rich logging
    log_workflow_start("adw_plan", adw_id, issue_number)

    try:
        # Initialize state
        state = ADWState(adw_id)
        state.update(issue_number=issue_number)
        state.save("adw_plan")

        ADWLogger.state_update(adw_id, "issue_number", issue_number)

        # Fetch issue
        ADWLogger.info("Fetching GitHub issue details...")
        issue = fetch_issue(issue_number)
        ADWLogger.info(f"Issue fetched: {issue.get('title')}")

        # Classify issue
        ADWLogger.separator("Issue Classification")
        ADWLogger.slash_command_start("/classify_issue", [str(issue_number)], adw_id)

        classify_result = run_slash_command("/classify_issue", adw_id, [str(issue_number)])

        if not classify_result.success:
            raise Exception(f"Classification failed: {classify_result.error}")

        issue_class = classify_result.data.get("issue_class", "/feature")
        state.update(issue_class=issue_class)
        state.save("adw_plan")

        ADWLogger.state_update(adw_id, "issue_class", issue_class)

        # Create branch
        ADWLogger.separator("Branch Creation")
        branch_name = f"feature/{issue_number}-{issue.get('title', 'untitled')}"
        create_branch(branch_name)

        ADWLogger.git_operation("Branch Created", branch_name)

        # Generate plan
        ADWLogger.separator("Plan Generation")

        # Get model for planning
        model = get_model_for_slash_command(
            AgentTemplateRequest(
                agent_name="planner",
                slash_command="/plan",
                args=[str(issue_number)],
                adw_id=adw_id
            )
        )

        ADWLogger.model_selection("/plan", state.get("model_set", "base"), model)

        plan_result = run_slash_command(
            "/plan",
            adw_id,
            [str(issue_number)],
            model=model
        )

        if not plan_result.success:
            raise Exception(f"Planning failed: {plan_result.error}")

        plan_file = plan_result.data.get("plan_file")
        state.update(plan_file=plan_file)
        state.save("adw_plan")

        ADWLogger.tool_call("Write", file_path=plan_file)
        ADWLogger.state_update(adw_id, "plan_file", plan_file)

        # Complete workflow
        log_workflow_complete("adw_plan", adw_id, success=True)

    except Exception as e:
        log_error("Workflow failed", e)
        log_workflow_complete("adw_plan", adw_id, success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Output Example

When you run this workflow, you'll see:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 Starting Workflow: adw_plan                                 ┃
┠────────────────────────────────────────────────────────────────┨
┃ ADW ID: adw-42                                                 ┃
┃ Issue: #42                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

ℹ️  State Update [adw-42]: issue_number = 42
ℹ️  Fetching GitHub issue details...
ℹ️  Issue fetched: Add dark mode toggle to settings

──────────────────── Issue Classification ────────────────────

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 Executing Slash Command                                     ┃
┠────────────────────────────────────────────────────────────────┨
┃ Command      /classify_issue                                   ┃
┃ ADW ID       adw-42                                            ┃
┃ Model        sonnet                                            ┃
┃ Args         42                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

ℹ️  State Update [adw-42]: issue_class = /feature

──────────────────── Branch Creation ────────────────────

🔀 Git Branch Created: feature/42-add-dark-mode-toggle

──────────────────── Plan Generation ────────────────────

🎯 Model Selection: /plan → base set → sonnet

📝 Write: `agents/adw-42/plan.md`
ℹ️  State Update [adw-42]: plan_file = agents/adw-42/plan.md

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🎉 Workflow Completed Successfully: adw_plan                   ┃
┠────────────────────────────────────────────────────────────────┨
┃ ADW ID: adw-42                                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## GitHub Actions Output

Rich console output works great in GitHub Actions! Here's what it looks like:

### Step 1: Add Rich to Workflow Dependencies

In your GitHub Actions workflow, the uv script dependencies will automatically install Rich:

```yaml
- name: Run ADW Plan
  run: |
    uv run adws/adw_plan.py ${{ github.event.issue.number }}
```

### Step 2: GitHub Actions Log Output

Rich automatically detects GitHub Actions and adjusts formatting. The output will show:

- ✅ Color-coded panels and text
- ✅ Emoji indicators for quick scanning
- ✅ Structured table layouts
- ✅ Clear visual hierarchy

**Screenshot equivalent** (GitHub Actions renders it with colors):

```
🚀 Starting Workflow: adw_plan
─────────────────────────────────────────────────
ADW ID: adw-42
Issue: #42
─────────────────────────────────────────────────

ℹ️  State Update [adw-42]: issue_number = 42
ℹ️  Fetching GitHub issue details...
ℹ️  Issue fetched: Add dark mode toggle to settings

──────────────────── Issue Classification ────────────────────

🚀 Executing Slash Command
─────────────────────────────────────────────────
Command      /classify_issue
ADW ID       adw-42
Model        sonnet
Args         42
─────────────────────────────────────────────────

ℹ️  State Update [adw-42]: issue_class = /feature

... (continues with colored output)
```

---

## Advanced Usage

### Configuration Tables

Display configuration nicely:

```python
config = {
    "adw_id": adw_id,
    "model_set": "heavy",
    "backend_port": 9100,
    "frontend_port": 9200,
}

ADWLogger.config_table("Workflow Configuration", config)
```

**Output**:
```
                Workflow Configuration
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Setting       ┃ Value        ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ adw_id        │ adw-42       │
│ model_set     │ heavy        │
│ backend_port  │ 9100         │
│ frontend_port │ 9200         │
└───────────────┴──────────────┘
```

### Code Blocks

Display code with syntax highlighting:

```python
plan_content = Path("agents/adw-42/plan.md").read_text()

ADWLogger.code_block(
    plan_content,
    language="markdown",
    title="Generated Plan"
)
```

### KPI Summary

Display KPIs in a nice table:

```python
kpis = {
    "current_streak": 5,
    "longest_streak": 12,
    "total_plan_size": 1500,
    "average_presence": 1.8,
}

ADWLogger.kpi_summary(kpis)
```

**Output**:
```
              📊 Agentic KPIs
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Metric            ┃ Value   ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Current Streak    │ 5       │
│ Longest Streak    │ 12      │
│ Total Plan Size   │ 1500    │
│ Average Presence  │ 1.8     │
└───────────────────┴─────────┘
```

### Progress Spinner

Show progress for long-running operations:

```python
with ADWLogger.progress_context("Running tests...") as progress:
    task = progress.add_task("Testing", total=100)
    # Do work
    progress.update(task, advance=50)
```

---

## Migration Checklist

### Phase 1: Setup (5 minutes)
- [x] Copy `adw_modules/rich_logging.py` to your project
- [ ] Add `"rich"` to script dependencies in workflow files
- [ ] Test with one workflow

### Phase 2: Core Workflows (1-2 hours)
- [ ] Update `adw_plan.py` with Rich logging
- [ ] Update `adw_build.py` with Rich logging
- [ ] Update `adw_test.py` with Rich logging
- [ ] Update `adw_review.py` with Rich logging

### Phase 3: ISO Workflows (1-2 hours)
- [ ] Update `adw_plan_iso.py`
- [ ] Update `adw_build_iso.py`
- [ ] Update `adw_test_iso.py`
- [ ] Update `adw_review_iso.py`

### Phase 4: Supporting Modules (1 hour)
- [ ] Update `agent.py` with tool call logging
- [ ] Update `state.py` with state update logging
- [ ] Update `github_utils.py` with git operation logging

### Phase 5: Testing (30 minutes)
- [ ] Test locally with `uv run`
- [ ] Test in GitHub Actions
- [ ] Verify log readability
- [ ] Check performance impact (should be minimal)

---

## Performance Considerations

Rich logging is very efficient:

- ✅ **Minimal overhead**: ~1-2ms per log statement
- ✅ **No file I/O**: Direct to stdout (same as standard logging)
- ✅ **GitHub Actions compatible**: Auto-detects CI environment
- ✅ **No breaking changes**: Works alongside existing logging

### Disable Rich (if needed)

If you need to disable Rich formatting:

```python
from rich.console import Console

# Disable color/formatting
console = Console(force_terminal=False, no_color=True)
```

Or set environment variable:

```bash
NO_COLOR=1 uv run adws/adw_plan.py 42
```

---

## Summary

### What You Get

1. **Better Readability**: Visual hierarchy with panels, tables, and colors
2. **Quick Scanning**: Emoji indicators for status at a glance
3. **Easier Debugging**: Clear structure shows workflow progression
4. **GitHub Actions**: Works great in CI/CD logs
5. **Zero Breaking Changes**: Fully backward compatible

### Implementation Steps

1. ✅ Add `"rich"` to script dependencies
2. ✅ Import `ADWLogger` from `adw_modules.rich_logging`
3. ✅ Replace `logger.info()` with `ADWLogger` methods
4. ✅ Test locally and in GitHub Actions

### Next Steps

1. Start with one workflow (e.g., `adw_plan.py`)
2. Run it and see the improved output
3. Gradually migrate other workflows
4. Share the pattern across all ADW scripts

**Total implementation time**: 2-4 hours for all workflows

**Impact**: Significantly better developer experience
