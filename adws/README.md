# AI Developer Workflow (ADW) System

**A meta-agentic development automation system that builds, tests, and improves software through GitHub integration.**

---

## 🚀 Quick Start - Common Workflows

**For humans: Use these commands for everyday tasks.**

### Process an Issue End-to-End

```bash
# Full workflow: Plan → Build → Test → Review → Document
uv run adws/adw_sdlc.py <issue-number>

# Example: Process issue #123
uv run adws/adw_sdlc.py 123
```

### Quick Workflows

```bash
# Just plan and build (fastest)
uv run adws/adw_plan_build.py <issue-number>

# Plan, build, and test
uv run adws/adw_plan_build_test.py <issue-number>

# Plan, build, test, and review (no docs)
uv run adws/adw_plan_build_test_review.py <issue-number>
```

### Auto-Process All New Issues

```bash
# Start monitoring (polls GitHub every 20 seconds)
uv run adws/adw_triggers/trigger_cron.py

# Or start webhook server (instant processing)
uv run adws/adw_triggers/trigger_webhook.py
```

### Run Individual Phases

```bash
# Planning only
uv run adws/adw_plan.py <issue-number>

# Implementation only (requires existing plan)
uv run adws/adw_build.py <issue-number> <adw-id>

# Testing only
uv run adws/adw_test.py <issue-number> <adw-id>

# Review only
uv run adws/adw_review.py <issue-number> <adw-id>

# Documentation only
uv run adws/adw_document.py <issue-number> <adw-id>
```

### Prerequisites

```bash
# Required environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_REPO_URL="https://github.com/owner/repo"

# Optional (defaults shown)
export CLAUDE_CODE_PATH="claude"  # Path to Claude Code CLI
export GITHUB_PAT="ghp_..."       # Only if using different account than 'gh auth'
```

---

## 📚 Complete System Documentation

**For AI systems and developers: Comprehensive reference of all capabilities.**

### Table of Contents

1. [System Overview](#system-overview)
2. [Key Concepts](#key-concepts)
3. [Workflow Types](#workflow-types)
4. [Meta-Agentic Capabilities](#meta-agentic-capabilities)
5. [State Management](#state-management)
6. [Command Reference](#command-reference)
7. [Architecture](#architecture)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

---

## System Overview

### What is ADW?

ADW (AI Developer Workflow) is a **Level 3-4 meta-agentic system** that:
- Automates complete software development lifecycles
- Processes GitHub issues from planning through deployment
- Runs workflows in parallel (up to 15x throughput via worktrees)
- Generates its own capabilities (meta-command generation)
- Tracks and optimizes its own performance (KPI dashboard)
- Self-extends and self-improves

### Capability Levels

**Level 0-1:** Basic automation (script execution)
**Level 2:** Multi-phase workflows (plan → build → test)
**Level 3:** Self-monitoring and optimization (KPI tracking, model selection)
**Level 4:** Self-extension (generates new slash commands)
**Level 5:** Autonomous operation (ZTE - Zero Touch Execution)

**Current ADW Status:** Level 3-4 (moving toward Level 5)

### Architecture Principles

1. **Composability** - Individual phases can run standalone or chained
2. **Isolation** - Worktrees enable parallel execution without conflicts
3. **Type Safety** - End-to-end Pydantic validation
4. **Observability** - All executions tracked with ADW IDs
5. **Self-Improvement** - System generates its own metrics and capabilities

---

## Key Concepts

### ADW ID

Each workflow run gets a unique 8-character identifier (e.g., `a1b2c3d4`).

**Purpose:**
- Tracks all phases of a workflow (plan → build → test → review → document)
- Appears in GitHub comments, commits, PR titles
- Creates isolated workspace at `agents/{adw_id}/`
- Enables resuming workflows and debugging
- Links related workflows in parallel execution

**Format:** `[a-f0-9]{8}` (lowercase hex)

**Example Tracking:**
```
Issue #123 → ADW ID: a1b2c3d4
├── Branch: feat-123-a1b2c3d4-add-user-auth
├── Workspace: agents/a1b2c3d4/
├── Plan: agents/a1b2c3d4/a1b2c3d4_plan_spec.md
├── PR: "feat: Add user authentication (a1b2c3d4)"
└── Commits: All tagged with a1b2c3d4
```

### State Management

ADW uses persistent state files (`agents/{adw_id}/adw_state.json`) to enable workflow composition and chaining.

**State Schema (10 fields):**

```python
{
  "adw_id": str,              # Unique workflow identifier
  "issue_number": str,        # GitHub issue being processed
  "branch_name": str,         # Git branch for changes
  "plan_file": str,           # Path to implementation plan
  "issue_class": str,         # Issue type (/chore, /bug, /feature)

  # Meta-agentic fields (NEW)
  "worktree_path": str,       # Isolated worktree path (for parallel execution)
  "backend_port": int,        # Allocated backend port (9100-9114)
  "frontend_port": int,       # Allocated frontend port (9200-9214)
  "model_set": str,           # "base" (sonnet) or "heavy" (opus)
  "all_adws": List[str]       # All ADW IDs in this workflow chain
}
```

**State Persistence:**
- Written by each workflow phase
- Read by subsequent phases
- Enables resuming after failures
- Tracks workflow history

**State Passing:**
- Via stdin/stdout (piping)
- Via file (`agents/{adw_id}/adw_state.json`)
- Automatically managed by workflow scripts

### Workflow Composition

Workflows can be:

**1. Run Individually**
```bash
uv run adw_plan.py 123              # Planning only
uv run adw_build.py 123 a1b2c3d4    # Implementation only
uv run adw_test.py 123 a1b2c3d4     # Testing only
```

**2. Chained via Pipes**
```bash
uv run adw_plan.py 123 | uv run adw_build.py | uv run adw_test.py
# State flows automatically through stdin/stdout
```

**3. Combined in Orchestrators**
```bash
uv run adw_plan_build.py 123        # Plan + Build
uv run adw_sdlc.py 123              # All phases
```

**4. Run in Parallel (ISO workflows)**
```bash
# Run 5 issues simultaneously in isolated worktrees
uv run adw_plan_build_iso.py 101 &
uv run adw_plan_build_iso.py 102 &
uv run adw_plan_build_iso.py 103 &
uv run adw_plan_build_iso.py 104 &
uv run adw_plan_build_iso.py 105 &
wait
# Each gets unique ports, isolated workspace
```

---

## Workflow Types

### Standard Workflows

**Purpose:** Single execution environment, sequential processing
**Use When:** Processing issues one at a time
**Workspace:** Main repository directory

**Available Workflows:**

```bash
# Individual Phases
adw_plan.py              # Planning phase
adw_build.py             # Implementation phase
adw_test.py              # Testing phase
adw_review.py            # Review phase
adw_document.py          # Documentation phase
adw_patch.py             # Quick patch workflow

# Orchestrators
adw_plan_build.py                    # Plan → Build
adw_plan_build_test.py               # Plan → Build → Test
adw_plan_build_review.py             # Plan → Build → Review
adw_plan_build_test_review.py        # Plan → Build → Test → Review
adw_plan_build_document.py           # Plan → Build → Document
adw_sdlc.py                          # Plan → Build → Test → Review → Document
```

### ISO Workflows (Isolated Execution)

**Purpose:** Parallel execution in isolated worktrees
**Use When:** Processing multiple issues simultaneously (15x throughput)
**Workspace:** Dedicated worktree per ADW ID
**Ports:** Dynamically allocated (9100-9114 backend, 9200-9214 frontend)

**Key Differences from Standard:**
- ✅ Creates isolated git worktree
- ✅ Allocates unique ports (no conflicts)
- ✅ Writes `.ports.env` for app configuration
- ✅ Enables true parallel execution
- ✅ Zero interference between workflows

**Available ISO Workflows (14 total):**

```bash
# Individual Phases
adw_plan_iso.py          # Planning phase (isolated)
adw_build_iso.py         # Implementation phase (isolated)
adw_test_iso.py          # Testing phase (isolated)
adw_review_iso.py        # Review phase (isolated)
adw_document_iso.py      # Documentation phase (isolated)
adw_patch_iso.py         # Quick patch workflow (isolated)

# Orchestrators
adw_plan_build_iso.py                # Plan → Build (isolated)
adw_plan_build_test_iso.py           # Plan → Build → Test (isolated)
adw_plan_build_review_iso.py         # Plan → Build → Review (isolated)
adw_plan_build_test_review_iso.py    # Plan → Build → Test → Review (isolated)
adw_plan_build_document_iso.py       # Plan → Build → Document (isolated)
adw_sdlc_iso.py                      # Full SDLC (isolated)
adw_sdlc_zte_iso.py                  # Full SDLC with Zero Touch Execution
adw_ship_iso.py                      # Build → Test → Deploy (isolated)
```

### Workflow Selection Matrix

| Scenario | Recommended Workflow | Why |
|----------|---------------------|-----|
| Single issue, quick fix | `adw_plan_build.py` | Fast, no testing overhead |
| Single issue, production code | `adw_sdlc.py` | Full validation, documentation |
| Multiple issues (5-15) | `adw_sdlc_iso.py` (parallel) | 15x throughput via worktrees |
| Hot fix needed | `adw_patch.py` | Skips planning, direct patch |
| Experimental feature | `adw_plan_build_test_iso.py` | Isolated, won't affect main |
| Documentation update | `adw_plan_build_document.py` | Skips testing, focuses on docs |
| Code review changes | `adw_build_iso.py` | Isolated implementation only |

---

## Meta-Agentic Capabilities

### 1. Worktree Isolation (Level 3)

**What It Does:**
Creates isolated git worktrees for each ADW run, enabling parallel execution without conflicts.

**Setup:**
```bash
# Install a worktree for ADW ID
/install_worktree <adw-id>

# Cleanup worktrees (removes completed/stale worktrees)
/cleanup_worktrees
```

**How It Works:**
```
Main Repo: /Users/you/project/
├── .git/
├── app/
└── adws/

Worktree 1: /Users/you/project/.worktrees/a1b2c3d4/
├── .git (linked to main)
├── .ports.env (BACKEND_PORT=9101, FRONTEND_PORT=9201)
├── app/ (isolated copy)
└── adws/ (isolated copy)

Worktree 2: /Users/you/project/.worktrees/e5f6g7h8/
├── .git (linked to main)
├── .ports.env (BACKEND_PORT=9102, FRONTEND_PORT=9202)
├── app/ (isolated copy)
└── adws/ (isolated copy)
```

**Port Allocation:**
- Backend: 9100-9114 (15 ports available)
- Frontend: 9200-9214 (15 ports available)
- Deterministic based on ADW ID hash
- No port conflicts possible

**Benefits:**
- Run 15 workflows simultaneously
- Zero interference between workflows
- Each workflow has dedicated dev server
- Safe parallel execution

### 2. Dynamic Model Selection (Level 3)

**What It Does:**
Automatically selects the optimal AI model based on task complexity and state configuration.

**Model Sets:**

| Model Set | Primary Model | Use Case | Cost | Speed |
|-----------|--------------|----------|------|-------|
| `base` | claude-sonnet-4.5 | Default, most tasks | Lower | Faster |
| `heavy` | claude-opus-4 | Complex implementation | Higher | Slower |

**Commands with Dynamic Selection:**

```python
# Uses heavy model in heavy mode, sonnet in base mode
COMMANDS_WITH_DYNAMIC_SELECTION = [
    "/implement",           # Implementation tasks
    "/resolve_failed_test", # Test failure resolution
    "/resolve_failed_e2e_test", # E2E test failures
    "/document",           # Documentation generation
    "/chore",              # Maintenance tasks
    "/bug",                # Bug fixes
    "/feature",            # New features
    "/patch"               # Quick patches
]

# Always uses sonnet (fast, efficient)
COMMANDS_ALWAYS_SONNET = [
    "/classify_issue",     # Issue classification
    "/classify_adw",       # ADW classification
    "/review",             # Code review
    "/test",               # Test execution
    "/start",              # App startup
    "/install"             # Dependency installation
]
```

**Configuration:**

Set in state or issue body:
```json
{
  "model_set": "heavy"  // Use opus for complex tasks
}
```

Or let classifier decide automatically based on issue complexity.

**Location:** `adws/adw_modules/agent.py` - `get_model_for_slash_command()`

### 3. KPI Tracking Dashboard (Level 3)

**What It Does:**
Tracks system performance metrics and generates performance dashboards.

**Command:**
```bash
/track_agentic_kpis <state-json>
```

**Metrics Tracked:**

**Agentic KPIs (Summary):**
- Current Streak (consecutive workflows with ≤2 attempts)
- Longest Streak
- Total Plan Size (lines of planning)
- Largest Plan Size
- Total Diff Size (lines changed)
- Largest Diff Size
- Average Presence (average attempts per workflow)

**ADW KPIs (Per Workflow):**
- Date
- ADW ID
- Issue Number
- Issue Class
- Attempts (how many plan/patch iterations)
- Plan Size (lines)
- Diff Size (added/removed/files)
- Created/Updated timestamps

**Output:**
Creates/updates `app_docs/agentic_kpis.md` with formatted tables.

**Purpose:**
- Track system efficiency over time
- Identify optimization opportunities
- Measure autonomous operation success
- Build learning datasets

### 4. Meta-Command Generation (Level 4)

**What It Does:**
System generates its own new slash commands based on natural language descriptions.

**Command:**
```bash
/meta-command <command-name> "<description>"
```

**Example:**
```bash
/meta-command deploy-staging "Deploy current branch to staging environment with health checks"
```

**Output:**
- Creates `.claude/commands/deploy-staging.md`
- Follows Claude Code command conventions
- Includes proper frontmatter
- Self-documenting
- Ready to use immediately

**Capabilities:**
- Extends system without human coding
- Learns from existing command patterns
- Creates domain-specific workflows
- Self-improvement capability

**Location:** `meta-agent` in `.claude/agents/`

### 5. Health Check System (Level 3)

**What It Does:**
Validates ADW system health and identifies configuration issues.

**Command:**
```bash
/health_check
```

**Checks:**
- Environment variables (ANTHROPIC_API_KEY, GITHUB_REPO_URL, etc.)
- Claude Code CLI installation
- GitHub authentication
- Python dependencies (uv)
- Core modules import successfully
- Workflow files exist and are executable
- State directory is writable
- Git configuration

**Output:**
```
ADW Health Check Results
========================

✅ Environment Variables
✅ Claude Code CLI (v1.2.3)
✅ GitHub Authentication
✅ Python Dependencies
✅ Core Modules
✅ Workflow Files (28 workflows found)
✅ State Directory
✅ Git Configuration

Status: HEALTHY
All systems operational.
```

**Use Cases:**
- Troubleshooting setup issues
- Pre-deployment validation
- Continuous monitoring
- Template health verification

### 6. In-Loop Review (Level 3)

**What It Does:**
Continuously reviews implementation during build phase, catching issues early.

**Command:**
```bash
/in_loop_review <state-json>
```

**How It Works:**
1. Monitors implementation progress
2. Reviews code changes incrementally
3. Identifies issues before testing phase
4. Suggests improvements in real-time
5. Reduces test-fix cycles

**Benefits:**
- Earlier issue detection
- Faster overall workflow
- Better code quality
- Reduced rework

---

## State Management

### State Lifecycle

```
1. Workflow Start
   ↓
   ADW ID generated (e.g., a1b2c3d4)
   ↓
2. State Initialization
   ↓
   Create agents/a1b2c3d4/adw_state.json
   ↓
3. Phase Execution
   ↓
   Each phase reads/updates state
   ↓
4. State Persistence
   ↓
   Written after each phase
   ↓
5. Workflow Completion
   ↓
   Final state saved for history
```

### State File Structure

**Location:** `agents/{adw_id}/adw_state.json`

**Complete Schema:**

```json
{
  "adw_id": "a1b2c3d4",
  "issue_number": "123",
  "branch_name": "feat-123-a1b2c3d4-add-user-auth",
  "plan_file": "agents/a1b2c3d4/a1b2c3d4_plan_spec.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/.worktrees/a1b2c3d4",
  "backend_port": 9101,
  "frontend_port": 9201,
  "model_set": "base",
  "all_adws": ["a1b2c3d4", "e5f6g7h8"]
}
```

### State Operations

**Create State:**
```python
from adw_modules.state import ADWState

state = ADWState("a1b2c3d4")
state.update(
    issue_number="123",
    issue_class="/feature",
    model_set="base"
)
state.save()
```

**Load State:**
```python
state = ADWState.load("a1b2c3d4", logger)
if state:
    issue_number = state.get("issue_number")
    model_set = state.get("model_set", "base")
```

**Update State:**
```python
state.update(
    branch_name="feat-123-a1b2c3d4-add-auth",
    plan_file="agents/a1b2c3d4/a1b2c3d4_plan_spec.md"
)
state.save()
```

**Append ADW Tracking:**
```python
# Track related workflows
state.append_adw_id("e5f6g7h8")  # Add patch attempt
state.save()
```

---

## Command Reference

### Slash Commands (28+ commands)

**Development Workflows:**
- `/feature` - Implement new features
- `/bug` - Fix bugs
- `/chore` - Maintenance tasks
- `/patch` - Quick patches
- `/implement` - Direct implementation

**Testing & Quality:**
- `/test` - Run test suites
- `/test_e2e` - E2E browser tests
- `/review` - Code review
- `/resolve_failed_test` - Fix test failures
- `/resolve_failed_e2e_test` - Fix E2E failures
- `/in_loop_review` - Continuous review

**Documentation:**
- `/document` - Generate docs
- `/conditional_docs` - Conditional documentation

**Git Operations:**
- `/commit` - Create commits
- `/pull_request` - Create PRs
- `/generate_branch_name` - Generate semantic branch names

**Project Setup:**
- `/install` - Install dependencies
- `/install_worktree` - Setup worktree
- `/cleanup_worktrees` - Remove worktrees
- `/prepare_app` - Prepare app for testing
- `/start` - Start dev servers

**Classification:**
- `/classify_issue` - Classify issue type
- `/classify_adw` - Classify ADW workflow

**Meta-Agentic:**
- `/meta-command` - Generate new commands
- `/track_agentic_kpis` - Update KPI dashboard
- `/health_check` - System health validation

**Utilities:**
- `/tools` - List available tools
- `/prime` - Prime system with context

### Workflow Scripts

**Standard Workflows (11 scripts):**
```bash
adw_plan.py                      # Planning phase
adw_build.py                     # Implementation phase
adw_test.py                      # Testing phase
adw_review.py                    # Review phase
adw_document.py                  # Documentation phase
adw_patch.py                     # Quick patch workflow
adw_plan_build.py                # Plan + Build
adw_plan_build_test.py           # Plan + Build + Test
adw_plan_build_review.py         # Plan + Build + Review
adw_plan_build_test_review.py    # Plan + Build + Test + Review
adw_plan_build_document.py       # Plan + Build + Document
adw_sdlc.py                      # Complete SDLC
```

**ISO Workflows (14 scripts):**
```bash
adw_plan_iso.py                  # Planning (isolated)
adw_build_iso.py                 # Implementation (isolated)
adw_test_iso.py                  # Testing (isolated)
adw_review_iso.py                # Review (isolated)
adw_document_iso.py              # Documentation (isolated)
adw_patch_iso.py                 # Quick patch (isolated)
adw_plan_build_iso.py            # Plan + Build (isolated)
adw_plan_build_test_iso.py       # Plan + Build + Test (isolated)
adw_plan_build_review_iso.py     # Plan + Build + Review (isolated)
adw_plan_build_test_review_iso.py # Plan + Build + Test + Review (isolated)
adw_plan_build_document_iso.py   # Plan + Build + Document (isolated)
adw_sdlc_iso.py                  # Complete SDLC (isolated)
adw_sdlc_zte_iso.py              # SDLC with Zero Touch Execution
adw_ship_iso.py                  # Build + Test + Deploy (isolated)
```

**Triggers (2 scripts):**
```bash
adw_triggers/trigger_cron.py     # Polling monitor
adw_triggers/trigger_webhook.py  # Webhook server
```

---

## Architecture

### Module Structure

```
adws/
├── adw_modules/              # Core library
│   ├── __init__.py
│   ├── agent.py              # Claude Code CLI integration
│   ├── data_types.py         # Pydantic models
│   ├── git_ops.py            # Git operations (with cwd support)
│   ├── github.py             # GitHub API operations
│   ├── r2_uploader.py        # Cloud storage for artifacts
│   ├── state.py              # State management
│   ├── utils.py              # Utility functions
│   ├── workflow_ops.py       # Core workflow operations
│   └── worktree_ops.py       # Worktree isolation (NEW)
│
├── adw_tests/                # Test suites
│   ├── health_check.py       # System health validation
│   ├── test_agents.py        # Agent execution tests
│   ├── test_integration.py   # Integration tests
│   ├── test_model_selection.py # Model selection tests
│   ├── test_r2_uploader.py   # Cloud upload tests
│   └── test_webhook_simplified.py # Webhook validation
│
├── adw_triggers/             # Automation triggers
│   ├── trigger_cron.py       # Polling monitor
│   └── trigger_webhook.py    # Webhook server
│
├── adw_*.py                  # Standard workflows (11 files)
└── adw_*_iso.py              # ISO workflows (14 files)
```

### Core Components

**agent.py**
- Claude Code CLI integration
- Dynamic model selection
- Template request building
- Session management

**data_types.py**
- `AgentTemplateRequest` - Agent execution request
- `ADWStateData` - State schema with validation
- `ADWExtractionResult` - Workflow classification result
- Type safety via Pydantic v2

**git_ops.py**
- `get_current_branch(cwd)` - Get current branch
- `create_branch(name, cwd)` - Create feature branch
- `commit_changes(message, cwd)` - Create commits
- `push_branch(name, cwd)` - Push to remote
- `finalize_git_operations(state, logger, cwd)` - Complete git flow
- **NEW:** All functions support `cwd` parameter for worktree operations

**github.py**
- `get_issue_details(number)` - Fetch issue data
- `post_comment(number, body)` - Add comments
- `create_pull_request(state)` - Create PRs
- `update_pull_request(number, state)` - Update PRs

**state.py**
- `ADWState(adw_id)` - State container
- `update(**kwargs)` - Update state fields
- `save()` - Persist to file
- `load(adw_id)` - Load from file
- `from_stdin()` - Load from pipe
- `append_adw_id(id)` - Track related workflows
- `get_working_directory()` - Get worktree path

**workflow_ops.py**
- `extract_adw_info(text, temp_id)` - Classify workflow type
- Returns `ADWExtractionResult` with workflow_command, adw_id, model_set
- Uses `/classify_adw` command
- **NEW:** Extracts model_set for dynamic selection

**worktree_ops.py** (NEW)
- `get_ports_for_adw(adw_id)` - Allocate unique ports
- `create_ports_env(worktree_path, backend, frontend)` - Create .ports.env
- `setup_worktree(adw_id, branch)` - Initialize worktree
- Port range: 9100-9114 (backend), 9200-9214 (frontend)
- Deterministic allocation via hash

**utils.py**
- `make_adw_id()` - Generate 8-char UUID
- `setup_logger(adw_id, trigger)` - Configure logging
- `parse_json(text, type)` - Parse JSON from markdown
- `check_env_vars(logger)` - Validate environment
- `get_safe_subprocess_env()` - Filter env vars for security

### Data Flow

```
GitHub Issue
     ↓
trigger_cron.py / trigger_webhook.py
     ↓
extract_adw_info() → [workflow_command, adw_id, model_set]
     ↓
ADWState.create(adw_id)
     ↓
[ISO workflow? → setup_worktree()]
     ↓
Phase 1: Planning
  - /classify_issue → issue_class
  - /feature | /bug | /chore → plan
  - create_branch()
  - commit_changes()
     ↓
Phase 2: Implementation
  - get_model_for_slash_command() → model selection
  - /implement → code changes
  - commit_changes()
     ↓
Phase 3: Testing
  - /test → test suite
  - /resolve_failed_test (if needed)
  - commit_changes()
     ↓
Phase 4: Review
  - /review → validation report
  - /resolve_failed_test (blockers)
  - upload screenshots
     ↓
Phase 5: Documentation
  - /document → docs generation
  - commit to app_docs/
     ↓
finalize_git_operations()
  - push_branch()
  - create_pull_request()
     ↓
[ISO workflow? → cleanup_worktree (optional)]
     ↓
/track_agentic_kpis → Update dashboard
```

---

## Configuration

### Environment Variables

**Required:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_REPO_URL="https://github.com/owner/repo"
```

**Optional:**
```bash
export CLAUDE_CODE_PATH="claude"              # Default: "claude"
export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR="true"  # Maintain working directory
export GITHUB_PAT="ghp_..."                   # Only if not using 'gh auth'
export E2B_API_KEY="..."                      # For cloud sandboxes (optional)
export CLOUDFLARED_TUNNEL_TOKEN="..."         # For tunnel access (optional)
```

### Model Configuration

**Edit:** `adws/adw_modules/agent.py`

**Model Selection Map:**
```python
SLASH_COMMAND_MODEL_MAP = {
    "/implement": {"base": "sonnet", "heavy": "opus"},
    "/bug": {"base": "sonnet", "heavy": "opus"},
    "/feature": {"base": "sonnet", "heavy": "opus"},
    "/patch": {"base": "sonnet", "heavy": "opus"},
    "/document": {"base": "sonnet", "heavy": "opus"},
    "/resolve_failed_test": {"base": "sonnet", "heavy": "opus"},
    "/resolve_failed_e2e_test": {"base": "sonnet", "heavy": "opus"},
    "/chore": {"base": "sonnet", "heavy": "opus"},

    # Always use sonnet (fast, efficient)
    "/classify_issue": {"base": "sonnet", "heavy": "sonnet"},
    "/classify_adw": {"base": "sonnet", "heavy": "sonnet"},
    "/review": {"base": "sonnet", "heavy": "sonnet"},
    "/test": {"base": "sonnet", "heavy": "sonnet"},
}
```

**Model Names:**
- `"sonnet"` → `claude-sonnet-4.5-20250929`
- `"opus"` → `claude-opus-4-20250514`

### Webhook Configuration

**Setup GitHub Webhook:**

1. Go to: `https://github.com/owner/repo/settings/hooks`
2. Click "Add webhook"
3. Configure:
   - **Payload URL:** `https://your-domain.com/gh-webhook`
   - **Content type:** `application/json`
   - **Secret:** Generate and save as `GITHUB_WEBHOOK_SECRET`
   - **Events:** Issues, Issue comments
4. Save

**Start Webhook Server:**
```bash
export GITHUB_WEBHOOK_SECRET="your-secret-here"
uv run adws/adw_triggers/trigger_webhook.py
```

**Verify:**
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy"}
```

### Port Configuration

**Worktree Ports:**
- Backend: 9100-9114 (15 available)
- Frontend: 9200-9214 (15 available)

**Port Allocation:**
- Deterministic based on ADW ID hash
- No manual configuration needed
- Automatically written to `.ports.env` in worktree

**Example `.ports.env`:**
```bash
BACKEND_PORT=9101
FRONTEND_PORT=9201
```

---

## Troubleshooting

### Health Check First

```bash
/health_check
```

This validates:
- Environment variables
- Claude Code installation
- GitHub authentication
- Dependencies
- Workflow files
- System configuration

### Common Issues

#### "Claude Code CLI is not installed"
```bash
# Check installation
which claude

# Install from https://docs.anthropic.com/en/docs/claude-code
```

#### "Missing ANTHROPIC_API_KEY"
```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify
echo $ANTHROPIC_API_KEY
```

#### "GitHub authentication failed"
```bash
# Authenticate with GitHub CLI
gh auth login

# Verify
gh auth status
```

#### "Module not found" errors
```bash
# Install with uv
cd adws
uv sync --all-extras

# Verify
uv run python -c "from adw_modules import state; print('OK')"
```

#### "Port already in use" (ISO workflows)
```bash
# Check allocated ports
cat .worktrees/*/ports.env

# Kill process on port
lsof -ti:9101 | xargs kill -9

# Or cleanup worktrees
/cleanup_worktrees
```

#### "Worktree creation failed"
```bash
# Check git worktree list
git worktree list

# Remove stale worktrees
git worktree prune

# Manual cleanup
rm -rf .worktrees/<adw-id>
git worktree remove .worktrees/<adw-id>
```

#### "Agent execution timeout"
```bash
# Check logs
cat agents/<adw-id>/*/raw_output.jsonl | tail -1 | jq .

# Common causes:
# - Model overload (switch to sonnet)
# - Network issues (check connection)
# - Complex task (use heavy model set)
```

### Debug Mode

```bash
# Enable verbose logging
export ADW_DEBUG=true

# Run workflow
uv run adws/adw_plan_build.py 123

# Check execution logs
cat agents/<adw-id>/*/execution.log
```

### Workflow Output Structure

Each workflow creates diagnostic outputs:

```
agents/<adw-id>/
├── adw_state.json              # State file
├── <adw-id>_plan_spec.md       # Implementation plan
├── planner/
│   ├── execution.log           # Planning logs
│   └── raw_output.jsonl        # Claude Code session
├── implementor/
│   ├── execution.log
│   └── raw_output.jsonl
├── tester/
│   ├── execution.log
│   └── raw_output.jsonl
├── reviewer/
│   ├── execution.log
│   ├── raw_output.jsonl
│   └── review_img/             # Screenshots
└── documenter/
    ├── execution.log
    └── raw_output.jsonl
```

### Getting Help

1. **Check Logs:** `agents/<adw-id>/*/execution.log`
2. **Run Health Check:** `/health_check`
3. **View Raw Output:** `cat agents/<adw-id>/*/raw_output.jsonl | jq .`
4. **Check State:** `cat agents/<adw-id>/adw_state.json | jq .`
5. **Test Integration:** `uv run adws/adw_tests/test_integration.py`

---

## Advanced Usage

### Parallel Execution Example

**Process 10 issues simultaneously:**

```bash
#!/bin/bash
# process_batch.sh

issues=(101 102 103 104 105 106 107 108 109 110)

for issue in "${issues[@]}"; do
    uv run adws/adw_sdlc_iso.py "$issue" &
done

wait

echo "All issues processed!"
/track_agentic_kpis
```

**Result:**
- 10 isolated worktrees created
- Unique ports allocated to each
- Parallel execution (10x faster than sequential)
- Zero interference
- KPI dashboard updated with metrics

### Custom Workflow Creation

**Generate new workflow via meta-command:**

```bash
/meta-command deploy-production "Build, test, and deploy to production with rollback capability"
```

**Result:**
- Creates `.claude/commands/deploy-production.md`
- Includes all deployment steps
- Ready to use immediately
- Self-documenting

### KPI Dashboard Automation

**Auto-update KPI dashboard after each workflow:**

```bash
# Add to workflow completion
uv run adws/adw_sdlc.py 123
/track_agentic_kpis "$(cat agents/<adw-id>/adw_state.json)"
```

**View dashboard:**
```bash
cat app_docs/agentic_kpis.md
```

### Continuous Monitoring Setup

**Option 1: Cron-based (polling every 20s)**
```bash
# Start monitor
nohup uv run adws/adw_triggers/trigger_cron.py > /tmp/adw_cron.log 2>&1 &
```

**Option 2: Webhook (instant processing)**
```bash
# Start webhook server
export GITHUB_WEBHOOK_SECRET="your-secret"
nohup uv run adws/adw_triggers/trigger_webhook.py > /tmp/adw_webhook.log 2>&1 &
```

---

## Performance Metrics

### Throughput Comparison

| Execution Mode | Issues/Hour | Workflows/Hour | Speedup |
|---------------|-------------|----------------|---------|
| Sequential (standard) | 1-2 | 1-2 | 1x (baseline) |
| Parallel (ISO, 5 workers) | 5-10 | 5-10 | 5x |
| Parallel (ISO, 10 workers) | 10-20 | 10-20 | 10x |
| Parallel (ISO, 15 workers) | 15-30 | 15-30 | 15x (max) |

### Cost Optimization

**Model Selection Impact:**

| Model Set | Model | Cost per 1M tokens | Avg Task Cost | Use Case |
|-----------|-------|-------------------|---------------|----------|
| base | sonnet-4.5 | $3 input / $15 output | $0.50-2.00 | Most workflows |
| heavy | opus-4 | $15 input / $75 output | $5.00-15.00 | Complex tasks only |

**Recommendation:**
- Use `base` (sonnet) for 90% of workflows
- Reserve `heavy` (opus) for:
  - Complex refactorings
  - Architecture changes
  - Critical bug fixes
  - Large feature implementations

---

## Security Best Practices

1. **Environment Variables**
   - Store all secrets in environment, never in code
   - Use `.env` files (never commit)
   - Rotate API keys regularly

2. **GitHub Tokens**
   - Use fine-grained tokens with minimal permissions
   - Required: `issues:write`, `pull_requests:write`, `contents:write`
   - Set expiration dates

3. **Branch Protection**
   - Require PR reviews for main branch
   - Enable status checks
   - Require signed commits (optional)

4. **Webhook Security**
   - Always use webhook secrets
   - Validate signatures on every request
   - Use HTTPS only
   - Rate limit webhook endpoint

5. **API Monitoring**
   - Set billing alerts in Anthropic dashboard
   - Monitor API usage via `/track_agentic_kpis`
   - Review costs regularly

6. **Access Control**
   - Limit who can trigger workflows
   - Use GitHub Teams for permissions
   - Audit workflow executions

---

## Contributing

### Running Tests

```bash
# Integration tests
uv run adws/adw_tests/test_integration.py

# Model selection tests
uv run adws/adw_tests/test_model_selection.py

# Webhook validation tests
uv run adws/adw_tests/test_webhook_simplified.py

# Agent execution tests
uv run adws/adw_tests/test_agents.py

# Health check
uv run adws/adw_tests/health_check.py

# All tests
uv run pytest adws/adw_tests/ -v
```

### Adding New Workflows

1. **Standard Workflow:**
   ```bash
   # Copy template
   cp adws/adw_plan.py adws/adw_new_workflow.py

   # Update workflow logic
   # Test
   uv run adws/adw_new_workflow.py 123
   ```

2. **ISO Workflow:**
   ```bash
   # Copy ISO template
   cp adws/adw_plan_iso.py adws/adw_new_workflow_iso.py

   # Update workflow logic
   # Test in isolation
   uv run adws/adw_new_workflow_iso.py 123
   ```

### Adding New Modules

```bash
# Create module
touch adws/adw_modules/new_module.py

# Add to __init__.py
echo "from . import new_module" >> adws/adw_modules/__init__.py

# Create tests
touch adws/adw_tests/test_new_module.py

# Implement and test
uv run adws/adw_tests/test_new_module.py
```

---

## Version History

**v2.0.0** (2025-10-05) - Meta-Agentic Upgrade
- Added ISO workflows (14 new workflows)
- Added worktree isolation support
- Added dynamic model selection
- Added KPI tracking dashboard
- Added meta-command generation
- Added health check system
- Added in-loop review
- Enhanced state management (10 fields)
- Performance: 15x throughput via parallel execution

**v1.0.0** (2025-01-01) - Initial Release
- Basic ADW workflows (11 workflows)
- Standard execution mode
- Simple state management (5 fields)
- Cron and webhook triggers
- GitHub integration

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Documentation:** This file
- **Issues:** GitHub Issues
- **Health Check:** Run `/health_check` command
- **Tests:** Run integration tests in `adws/adw_tests/`
