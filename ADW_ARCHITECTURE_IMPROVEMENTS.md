# ADW System Architecture Improvements Plan

**Document Version:** 1.0
**Date:** 2025-10-05
**System:** AI Developer Workflow (ADW) Meta-Agentic System
**Current Level:** 3-4 (moving toward Level 5)

---

## Executive Summary

The ADW system demonstrates excellent architectural fundamentals with clean separation of concerns, type safety, composability, and innovative parallel execution via ISO worktrees. However, critical gaps exist in **operational resilience** (state management, error recovery, resource limits) and **learning systems** (feedback loops, optimization).

**Verdict:** System is production-ready for <10 workflows/day. For 100+ workflows/day or autonomous operation, critical issues (Priority 1-2) must be addressed.

---

## Current Strengths

- ✅ **Separation of Concerns**: Clean orchestration (Python) vs execution (Claude Code)
- ✅ **Type Safety**: End-to-end Pydantic validation
- ✅ **Composability**: Individual phases can run standalone or chained
- ✅ **Parallel Execution**: ISO worktrees enable 15x throughput
- ✅ **Observability**: ADW IDs, structured logs, KPI tracking
- ✅ **Meta-Agentic Capabilities**: Self-extension, model selection, worktree isolation

---

## Implementation Priority

### Priority 1: Critical (Week 1-2)
- [ ] Issue #1: State Management Rewrite
- [ ] Issue #2: Execution Engine Abstraction

### Priority 2: High (Week 3-4)
- [ ] Issue #3: Resource Management
- [ ] Issue #4: Advanced Error Recovery

### Priority 3: Medium (Month 2)
- [ ] Issue #5: Enhanced Observability
- [ ] Issue #6: Feedback Loop System

### Priority 4: Strategic (Month 3)
- [ ] Issue #7: Declarative Workflows
- [ ] Issue #8: Adapter Pattern
- [ ] Issue #9: Security Hardening

---

# Issue #1: State Management Race Conditions (CRITICAL)

## Problem Description

**Current Implementation:**
```python
# adws/adw_modules/state.py:74-96
def save(self):
    state_path = self.get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    with open(state_path, "w") as f:
        json.dump(state_data.model_dump(), f, indent=2)
```

**What Breaks:**
- ✗ 15 parallel workflows = race conditions on file writes
- ✗ No atomic updates = corrupted state files
- ✗ No versioning = cannot rollback bad state
- ✗ File I/O failures = permanently lost state
- ✗ No transactional guarantees across multiple state updates

**Real-World Failure Scenario:**
```
Workflow A (adw-001) reads state → issue_number: 123
Workflow B (adw-002) reads state → issue_number: 456
Workflow A writes state (takes 50ms)
Workflow B writes state (overwrites A's write)
Result: Lost data from Workflow A
```

## Solution: SQLite-Based State Management

### Implementation Checklist

#### Step 1.1: Create New State Backend
- [ ] Create `adws/adw_modules/state_db.py`
- [ ] Implement SQLite schema with versioning
- [ ] Add automatic migration system
- [ ] Write unit tests for concurrent access

**Code to Implement:**
```python
# adws/adw_modules/state_db.py
"""SQLite-based state management with ACID guarantees."""

import sqlite3
import json
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

class ADWStateDB:
    """Thread-safe state management using SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database. Defaults to project_root/agents/adw_state.db
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "agents" / "adw_state.db"

        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Enable WAL mode for better concurrency
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    adw_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL DEFAULT 1,
                    data JSON NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            # State history for rollback capability
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adw_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    data JSON NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (adw_id) REFERENCES state(adw_id)
                )
            """)

            # Index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_adw_id
                ON state(adw_id)
            """)

            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # Wait up to 30s for lock
            isolation_level='IMMEDIATE'  # Prevent deadlocks
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save(self, adw_id: str, data: Dict[str, Any]) -> int:
        """Save state atomically with versioning.

        Args:
            adw_id: Unique workflow identifier
            data: State data to save

        Returns:
            New version number
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            # Check if state exists
            cursor = conn.execute(
                "SELECT version FROM state WHERE adw_id = ?",
                (adw_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing state
                new_version = row['version'] + 1

                # Archive old version to history
                old_state = conn.execute(
                    "SELECT data FROM state WHERE adw_id = ?",
                    (adw_id,)
                ).fetchone()

                conn.execute("""
                    INSERT INTO state_history (adw_id, version, data, created_at)
                    VALUES (?, ?, ?, ?)
                """, (adw_id, row['version'], old_state['data'], now))

                # Update current state
                conn.execute("""
                    UPDATE state
                    SET version = ?, data = ?, updated_at = ?
                    WHERE adw_id = ?
                """, (new_version, json.dumps(data), now, adw_id))
            else:
                # Insert new state
                new_version = 1
                conn.execute("""
                    INSERT INTO state (adw_id, version, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (adw_id, new_version, json.dumps(data), now, now))

            conn.commit()
            return new_version

    def load(self, adw_id: str) -> Optional[Dict[str, Any]]:
        """Load current state for ADW ID.

        Args:
            adw_id: Unique workflow identifier

        Returns:
            State data or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT data FROM state WHERE adw_id = ?",
                (adw_id,)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row['data'])
            return None

    def get_version(self, adw_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Load specific version of state from history.

        Args:
            adw_id: Unique workflow identifier
            version: Version number to load

        Returns:
            State data at specified version or None
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT data FROM state_history
                WHERE adw_id = ? AND version = ?
            """, (adw_id, version))
            row = cursor.fetchone()

            if row:
                return json.loads(row['data'])
            return None

    def rollback(self, adw_id: str, version: int) -> bool:
        """Rollback state to previous version.

        Args:
            adw_id: Unique workflow identifier
            version: Version to rollback to

        Returns:
            True if rollback successful
        """
        old_state = self.get_version(adw_id, version)
        if old_state is None:
            return False

        self.save(adw_id, old_state)
        return True
```

#### Step 1.2: Update State Module
- [ ] Modify `adws/adw_modules/state.py` to use SQLite backend
- [ ] Maintain backward compatibility with file-based state
- [ ] Add migration tool to convert existing file states to DB

**Code to Implement:**
```python
# adws/adw_modules/state.py (updated)
"""State management for ADW composable architecture.

Provides persistent state management via SQLite (recommended)
or file storage (legacy) with transient state passing via stdin/stdout.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from adw_modules.data_types import ADWStateData
from adw_modules.state_db import ADWStateDB

# Global database instance (lazy initialization)
_db_instance: Optional[ADWStateDB] = None

def get_state_db() -> ADWStateDB:
    """Get or create global state database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ADWStateDB()
    return _db_instance

class ADWState:
    """Container for ADW workflow state with SQLite persistence."""

    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str, use_db: bool = True):
        """Initialize ADWState with a required ADW ID.

        Args:
            adw_id: The ADW ID for this state (required)
            use_db: Use SQLite backend (default: True). Set to False for legacy file-based state.
        """
        if not adw_id:
            raise ValueError("adw_id is required for ADWState")

        self.adw_id = adw_id
        self.use_db = use_db
        self.data: Dict[str, Any] = {"adw_id": self.adw_id}
        self.logger = logging.getLogger(__name__)
        self.db = get_state_db() if use_db else None

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state atomically to SQLite or file.

        Args:
            workflow_step: Optional workflow step name for logging
        """
        if self.use_db:
            # Save to SQLite (atomic, versioned)
            version = self.db.save(self.adw_id, self.data)
            self.logger.info(f"Saved state to database (version {version})")
        else:
            # Legacy file-based save
            self._save_to_file()

        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    def _save_to_file(self) -> None:
        """Legacy file-based state save."""
        state_path = self._get_file_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        state_data = ADWStateData(
            adw_id=self.data.get("adw_id"),
            issue_number=self.data.get("issue_number"),
            branch_name=self.data.get("branch_name"),
            plan_file=self.data.get("plan_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            backend_port=self.data.get("backend_port"),
            frontend_port=self.data.get("frontend_port"),
            model_set=self.data.get("model_set", "base"),
            all_adws=self.data.get("all_adws", []),
        )

        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")

    # ... rest of methods remain the same ...
```

#### Step 1.3: Migration & Testing
- [ ] Create migration script: `adws/adw_modules/migrate_state_to_db.py`
- [ ] Test concurrent writes with 15 parallel workflows
- [ ] Verify rollback capability
- [ ] Update documentation

**Migration Script:**
```python
# adws/adw_modules/migrate_state_to_db.py
"""Migrate file-based states to SQLite database."""

import json
import os
from pathlib import Path
from state_db import ADWStateDB

def migrate_all_states():
    """Migrate all file-based states to SQLite."""
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / "agents"

    if not agents_dir.exists():
        print("No agents directory found. Nothing to migrate.")
        return

    db = ADWStateDB()
    migrated = 0

    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        state_file = adw_dir / "adw_state.json"
        if not state_file.exists():
            continue

        try:
            with open(state_file) as f:
                data = json.load(f)

            adw_id = data.get("adw_id")
            if adw_id:
                db.save(adw_id, data)
                print(f"✓ Migrated {adw_id}")
                migrated += 1
        except Exception as e:
            print(f"✗ Failed to migrate {adw_dir.name}: {e}")

    print(f"\nMigration complete: {migrated} states migrated to SQLite")

if __name__ == "__main__":
    migrate_all_states()
```

#### Step 1.4: Validation
- [ ] Run migration on test data
- [ ] Verify all existing workflows work with SQLite backend
- [ ] Benchmark: Compare file vs SQLite performance
- [ ] Document rollback procedures

**Success Criteria:**
- ✓ No state corruption under 15 parallel workflows
- ✓ Rollback capability tested and working
- ✓ Performance: <10ms for state save/load
- ✓ All existing workflows pass integration tests

---

# Issue #2: Claude Code Coupling (CRITICAL)

## Problem Description

**Current Implementation:**
```python
# adws/adw_modules/agent.py:269
cmd = [CLAUDE_PATH, "-p", request.prompt]
cmd.extend(["--model", request.model])
cmd.extend(["--output-format", "stream-json"])
```

**What Breaks:**
- ✗ Entire system depends on Claude Code CLI availability
- ✗ Cannot swap to alternative LLM providers
- ✗ Cannot run in environments without Claude Code
- ✗ Cannot mock for testing
- ✗ Vendor lock-in

**Risk:** If Claude Code CLI changes flags, introduces bugs, or becomes unavailable, entire ADW system stops working.

## Solution: Execution Engine Abstraction

### Implementation Checklist

#### Step 2.1: Define Execution Engine Protocol
- [ ] Create `adws/adw_modules/execution_engine.py`
- [ ] Define protocol interface for all execution engines
- [ ] Implement factory pattern for engine selection

**Code to Implement:**
```python
# adws/adw_modules/execution_engine.py
"""Abstract execution engine for LLM interactions."""

from typing import Protocol, Optional
from abc import ABC, abstractmethod
from adw_modules.data_types import AgentPromptRequest, AgentPromptResponse

class ExecutionEngine(Protocol):
    """Protocol for LLM execution engines."""

    def execute(self, request: AgentPromptRequest) -> AgentPromptResponse:
        """Execute a prompt and return response.

        Args:
            request: The prompt request configuration

        Returns:
            Response with output and success status
        """
        ...

    def check_installed(self) -> Optional[str]:
        """Check if engine is available.

        Returns:
            Error message if not available, None otherwise
        """
        ...

    def get_name(self) -> str:
        """Get engine name for logging."""
        ...


class BaseExecutionEngine(ABC):
    """Base class for execution engines."""

    @abstractmethod
    def execute(self, request: AgentPromptRequest) -> AgentPromptResponse:
        """Execute a prompt."""
        pass

    @abstractmethod
    def check_installed(self) -> Optional[str]:
        """Check if engine is available."""
        pass

    def get_name(self) -> str:
        """Get engine name."""
        return self.__class__.__name__
```

#### Step 2.2: Implement Claude Code Engine
- [ ] Create `adws/adw_modules/engines/claude_code_engine.py`
- [ ] Move existing Claude Code logic to this engine
- [ ] Maintain all current functionality

**Code to Implement:**
```python
# adws/adw_modules/engines/claude_code_engine.py
"""Claude Code CLI execution engine."""

import subprocess
import os
import json
from typing import Optional
from adw_modules.execution_engine import BaseExecutionEngine
from adw_modules.data_types import AgentPromptRequest, AgentPromptResponse

class ClaudeCodeEngine(BaseExecutionEngine):
    """Execution engine using Claude Code CLI."""

    def __init__(self, claude_path: Optional[str] = None):
        """Initialize Claude Code engine.

        Args:
            claude_path: Path to Claude Code CLI. Defaults to CLAUDE_CODE_PATH env var.
        """
        self.claude_path = claude_path or os.getenv("CLAUDE_CODE_PATH", "claude")

    def check_installed(self) -> Optional[str]:
        """Check if Claude Code CLI is installed."""
        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return f"Error: Claude Code CLI is not installed. Expected at: {self.claude_path}"
        except FileNotFoundError:
            return f"Error: Claude Code CLI is not installed. Expected at: {self.claude_path}"
        return None

    def execute(self, request: AgentPromptRequest) -> AgentPromptResponse:
        """Execute prompt using Claude Code CLI.

        This is the existing implementation from agent.py:252-341
        """
        # Check if installed
        error_msg = self.check_installed()
        if error_msg:
            return AgentPromptResponse(output=error_msg, success=False, session_id=None)

        # Save prompt
        self._save_prompt(request.prompt, request.adw_id, request.agent_name)

        # Create output directory
        output_dir = os.path.dirname(request.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Build command
        cmd = [self.claude_path, "-p", request.prompt]
        cmd.extend(["--model", request.model])
        cmd.extend(["--output-format", "stream-json"])
        cmd.append("--verbose")

        if request.dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        # Get environment
        env = self._get_claude_env()

        try:
            # Execute and pipe output
            with open(request.output_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=request.working_dir,
                )

            if result.returncode == 0:
                # Parse JSONL output
                messages, result_message = self._parse_jsonl_output(request.output_file)
                self._convert_jsonl_to_json(request.output_file)

                if result_message:
                    session_id = result_message.get("session_id")
                    is_error = result_message.get("is_error", False)
                    subtype = result_message.get("subtype", "")

                    if subtype == "error_during_execution":
                        error_msg = "Error during execution: Agent encountered an error and did not return a result"
                        return AgentPromptResponse(
                            output=error_msg,
                            success=False,
                            session_id=session_id
                        )

                    result_text = result_message.get("result", "")
                    return AgentPromptResponse(
                        output=result_text,
                        success=not is_error,
                        session_id=session_id
                    )
                else:
                    # No result message, return raw output
                    with open(request.output_file, "r") as f:
                        raw_output = f.read()
                    return AgentPromptResponse(
                        output=raw_output,
                        success=True,
                        session_id=None
                    )
            else:
                error_msg = f"Claude Code error: {result.stderr}"
                return AgentPromptResponse(output=error_msg, success=False, session_id=None)

        except subprocess.TimeoutExpired:
            error_msg = "Error: Claude Code command timed out"
            return AgentPromptResponse(output=error_msg, success=False, session_id=None)
        except Exception as e:
            error_msg = f"Error executing Claude Code: {e}"
            return AgentPromptResponse(output=error_msg, success=False, session_id=None)

    def _save_prompt(self, prompt: str, adw_id: str, agent_name: str):
        """Save prompt to file."""
        # Implementation from agent.py:177-201
        pass

    def _get_claude_env(self):
        """Get environment variables for Claude Code."""
        from adw_modules.utils import get_safe_subprocess_env
        return get_safe_subprocess_env()

    def _parse_jsonl_output(self, output_file: str):
        """Parse JSONL output."""
        # Implementation from agent.py:112-135
        pass

    def _convert_jsonl_to_json(self, jsonl_file: str):
        """Convert JSONL to JSON."""
        # Implementation from agent.py:138-158
        pass
```

#### Step 2.3: Implement Alternative Engines
- [ ] Create OpenAI engine: `adws/adw_modules/engines/openai_engine.py`
- [ ] Create mock engine for testing: `adws/adw_modules/engines/mock_engine.py`
- [ ] Document how to add new engines

**Mock Engine for Testing:**
```python
# adws/adw_modules/engines/mock_engine.py
"""Mock execution engine for testing."""

from adw_modules.execution_engine import BaseExecutionEngine
from adw_modules.data_types import AgentPromptRequest, AgentPromptResponse

class MockEngine(BaseExecutionEngine):
    """Mock engine that returns predefined responses."""

    def __init__(self, responses: dict = None):
        """Initialize mock engine.

        Args:
            responses: Dict mapping prompts to responses
        """
        self.responses = responses or {}
        self.call_count = 0

    def check_installed(self):
        """Mock is always available."""
        return None

    def execute(self, request: AgentPromptRequest) -> AgentPromptResponse:
        """Return mock response."""
        self.call_count += 1

        # Check if we have a mock response for this prompt
        response_text = self.responses.get(request.prompt, "Mock response")

        return AgentPromptResponse(
            output=response_text,
            success=True,
            session_id=f"mock-{self.call_count}"
        )
```

#### Step 2.4: Factory Pattern
- [ ] Create engine factory in `adws/adw_modules/engine_factory.py`
- [ ] Support environment variable for engine selection
- [ ] Add validation and error handling

**Code to Implement:**
```python
# adws/adw_modules/engine_factory.py
"""Factory for creating execution engines."""

import os
from typing import Optional
from adw_modules.execution_engine import ExecutionEngine
from adw_modules.engines.claude_code_engine import ClaudeCodeEngine
from adw_modules.engines.mock_engine import MockEngine

def get_execution_engine(engine_type: Optional[str] = None) -> ExecutionEngine:
    """Get execution engine based on configuration.

    Args:
        engine_type: Engine type override. If None, uses ADW_EXECUTION_ENGINE env var.

    Returns:
        Configured execution engine

    Raises:
        ValueError: If engine type is unknown
    """
    if engine_type is None:
        engine_type = os.getenv("ADW_EXECUTION_ENGINE", "claude_code")

    engine_type = engine_type.lower()

    if engine_type == "claude_code":
        return ClaudeCodeEngine()
    elif engine_type == "mock":
        return MockEngine()
    else:
        raise ValueError(f"Unknown execution engine: {engine_type}")
```

#### Step 2.5: Update Agent Module
- [ ] Refactor `adws/adw_modules/agent.py` to use engine factory
- [ ] Maintain backward compatibility
- [ ] Update all tests

**Code to Implement:**
```python
# adws/adw_modules/agent.py (updated)
"""Claude Code agent module for executing prompts programmatically."""

from adw_modules.engine_factory import get_execution_engine
from adw_modules.data_types import AgentPromptRequest, AgentPromptResponse

def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute prompt using configured execution engine.

    This function now uses the execution engine abstraction,
    allowing for different LLM providers.
    """
    engine = get_execution_engine()
    return engine.execute(request)

# Rest of the module remains the same...
```

#### Step 2.6: Testing & Validation
- [ ] Write unit tests for each engine
- [ ] Write integration tests with mock engine
- [ ] Verify backward compatibility with Claude Code
- [ ] Update documentation with engine configuration

**Test Example:**
```python
# adws/adw_tests/test_execution_engines.py
"""Tests for execution engine abstraction."""

import pytest
from adw_modules.data_types import AgentPromptRequest
from adw_modules.engines.mock_engine import MockEngine
from adw_modules.engine_factory import get_execution_engine

def test_mock_engine():
    """Test mock engine returns expected responses."""
    engine = MockEngine(responses={
        "/test": "Test passed"
    })

    request = AgentPromptRequest(
        prompt="/test",
        adw_id="test123",
        agent_name="tester",
        model="sonnet",
        output_file="/tmp/test.jsonl"
    )

    response = engine.execute(request)
    assert response.success
    assert response.output == "Test passed"

def test_engine_factory():
    """Test engine factory creates correct engine."""
    import os
    os.environ["ADW_EXECUTION_ENGINE"] = "mock"

    engine = get_execution_engine()
    assert isinstance(engine, MockEngine)
```

**Success Criteria:**
- ✓ Can swap engines via environment variable
- ✓ All tests pass with mock engine
- ✓ Existing Claude Code functionality unchanged
- ✓ Documentation updated with engine configuration

---

# Issue #3: Resource Management (HIGH PRIORITY)

## Problem Description

**Current State:**
- ✗ No limits on concurrent workflows
- ✗ No memory limits per worktree
- ✗ No CPU throttling
- ✗ No API rate limiting (GitHub, Anthropic)
- ✗ System can exhaust resources and crash

**Real-World Failure Scenario:**
```
Start 15 parallel workflows
Each workflow uses 2GB RAM
Total: 30GB RAM (exceeds available 16GB)
Result: System swaps to disk, becomes unresponsive
```

## Solution: Resource Manager with Limits

### Implementation Checklist

#### Step 3.1: Create Resource Manager
- [ ] Create `adws/adw_modules/resource_manager.py`
- [ ] Implement semaphore for concurrent workflow limits
- [ ] Add memory monitoring per workflow
- [ ] Add API rate limiting

**Code to Implement:**
```python
# adws/adw_modules/resource_manager.py
"""Resource management for ADW workflows."""

import asyncio
import psutil
import time
from typing import Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ResourceLimits:
    """Resource limits configuration."""
    max_concurrent_workflows: int = 15
    max_memory_per_workflow_mb: int = 2048
    max_total_memory_percent: float = 80.0
    github_requests_per_minute: int = 60
    anthropic_requests_per_minute: int = 50

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.tokens = max_requests
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            refill = elapsed * (self.max_requests / self.window_seconds)
            self.tokens = min(self.max_requests, self.tokens + refill)
            self.last_update = now

            # Wait if no tokens available
            while self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.window_seconds / self.max_requests)
                await asyncio.sleep(wait_time)

                # Refill after waiting
                now = time.time()
                elapsed = now - self.last_update
                refill = elapsed * (self.max_requests / self.window_seconds)
                self.tokens = min(self.max_requests, self.tokens + refill)
                self.last_update = now

            # Consume token
            self.tokens -= 1

class ResourceManager:
    """Manages resource allocation for ADW workflows."""

    def __init__(self, limits: Optional[ResourceLimits] = None):
        """Initialize resource manager.

        Args:
            limits: Resource limits configuration
        """
        self.limits = limits or ResourceLimits()
        self.semaphore = asyncio.Semaphore(self.limits.max_concurrent_workflows)

        # Rate limiters for external APIs
        self.github_limiter = RateLimiter(self.limits.github_requests_per_minute)
        self.anthropic_limiter = RateLimiter(self.limits.anthropic_requests_per_minute)

        # Track active workflows
        self.active_workflows: dict[str, dict] = {}
        self.lock = asyncio.Lock()

    def check_memory_available(self) -> bool:
        """Check if system memory is below threshold.

        Returns:
            True if memory is available, False otherwise
        """
        memory = psutil.virtual_memory()
        return memory.percent < self.limits.max_total_memory_percent

    async def wait_for_memory(self):
        """Wait until memory is available."""
        while not self.check_memory_available():
            await asyncio.sleep(5)  # Check every 5 seconds

    @asynccontextmanager
    async def acquire_workflow_slot(self, adw_id: str):
        """Acquire resources for a workflow.

        Args:
            adw_id: Workflow identifier

        Yields:
            Context manager for workflow execution
        """
        # Wait for available slot
        async with self.semaphore:
            # Wait for memory to be available
            await self.wait_for_memory()

            # Track workflow
            async with self.lock:
                self.active_workflows[adw_id] = {
                    'start_time': datetime.utcnow(),
                    'initial_memory': psutil.virtual_memory().percent
                }

            try:
                yield
            finally:
                # Release workflow
                async with self.lock:
                    if adw_id in self.active_workflows:
                        del self.active_workflows[adw_id]

    @asynccontextmanager
    async def acquire_github_rate_limit(self):
        """Acquire GitHub API rate limit token."""
        await self.github_limiter.acquire()
        yield

    @asynccontextmanager
    async def acquire_anthropic_rate_limit(self):
        """Acquire Anthropic API rate limit token."""
        await self.anthropic_limiter.acquire()
        yield

    def get_active_workflows(self) -> dict:
        """Get currently active workflows.

        Returns:
            Dict of active workflow IDs and metadata
        """
        return self.active_workflows.copy()

# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None

def get_resource_manager(limits: Optional[ResourceLimits] = None) -> ResourceManager:
    """Get or create global resource manager.

    Args:
        limits: Resource limits (only used on first call)

    Returns:
        Global resource manager instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager(limits)
    return _resource_manager
```

#### Step 3.2: Integrate with Workflows
- [ ] Update workflow scripts to use resource manager
- [ ] Add async/await support to workflow orchestrators
- [ ] Test with 15 parallel workflows

**Code to Implement:**
```python
# Example: adws/adw_sdlc_iso.py (updated)
"""Complete SDLC workflow with resource management."""

import asyncio
from adw_modules.resource_manager import get_resource_manager
from adw_modules.utils import make_adw_id, setup_logger

async def run_workflow_with_resources(issue_number: str):
    """Run workflow with resource management."""
    adw_id = make_adw_id()
    logger = setup_logger(adw_id, "sdlc_iso")
    resource_manager = get_resource_manager()

    # Acquire workflow slot
    async with resource_manager.acquire_workflow_slot(adw_id):
        logger.info(f"Acquired resources for workflow {adw_id}")

        try:
            # Run workflow phases...
            # Each phase that calls GitHub/Anthropic should use rate limiters

            # Example: GitHub API call
            async with resource_manager.acquire_github_rate_limit():
                issue = await get_issue_details(issue_number)

            # Example: Anthropic API call
            async with resource_manager.acquire_anthropic_rate_limit():
                response = await execute_template(request)

            logger.info(f"Workflow {adw_id} completed successfully")
        except Exception as e:
            logger.error(f"Workflow {adw_id} failed: {e}")
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: uv run adws/adw_sdlc_iso.py <issue-number>")
        sys.exit(1)

    issue_number = sys.argv[1]
    asyncio.run(run_workflow_with_resources(issue_number))
```

#### Step 3.3: Add Monitoring Dashboard
- [ ] Create `/status` endpoint showing active workflows
- [ ] Add memory usage tracking
- [ ] Add rate limit status display

**Code to Implement:**
```python
# adws/adw_triggers/status_api.py
"""Status API for monitoring ADW workflows."""

from fastapi import FastAPI
from adw_modules.resource_manager import get_resource_manager
import psutil

app = FastAPI()

@app.get("/status")
async def get_status():
    """Get current system status."""
    resource_manager = get_resource_manager()
    memory = psutil.virtual_memory()

    return {
        "active_workflows": len(resource_manager.active_workflows),
        "max_workflows": resource_manager.limits.max_concurrent_workflows,
        "memory_percent": memory.percent,
        "memory_threshold": resource_manager.limits.max_total_memory_percent,
        "workflows": resource_manager.get_active_workflows()
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
```

#### Step 3.4: Testing & Validation
- [ ] Load test with 20 parallel workflows (should queue)
- [ ] Verify memory limits enforced
- [ ] Test rate limiting with API calls
- [ ] Monitor system stability

**Success Criteria:**
- ✓ System remains stable with 20+ parallel workflow requests
- ✓ Memory never exceeds configured threshold
- ✓ API rate limits respected
- ✓ Workflows queue gracefully when at capacity

---

# Issue #4: Advanced Error Recovery (HIGH PRIORITY)

## Problem Description

**Current Implementation:**
```python
# adws/adw_modules/agent.py:228
for attempt in range(max_retries + 1):
    response = prompt_claude_code(request)
    if response.success:
        return response
```

**Missing:**
- ✗ Exponential backoff (constant retry intervals cause thundering herd)
- ✗ Circuit breakers (keeps retrying when service is down)
- ✗ Dead letter queue (failed workflows lost)
- ✗ Idempotency (retries may create duplicate work)

## Solution: Resilient Error Recovery System

### Implementation Checklist

#### Step 4.1: Implement Circuit Breaker
- [ ] Create `adws/adw_modules/circuit_breaker.py`
- [ ] Add state tracking (closed, open, half-open)
- [ ] Implement failure threshold and recovery timeout

**Code to Implement:**
```python
# adws/adw_modules/circuit_breaker.py
"""Circuit breaker pattern for fault tolerance."""

import time
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures exceeded threshold, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds to wait before retry
    success_threshold: int = 2          # Successes to close from half-open

class CircuitBreaker:
    """Circuit breaker for external service calls."""

    def __init__(self, config: CircuitBreakerConfig = None):
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def is_open(self) -> bool:
        """Check if circuit is open (rejecting calls).

        Returns:
            True if circuit is open
        """
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    # Try half-open state
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return False
            return True
        return False

    def record_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                # Service recovered, close circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record failed call."""
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery attempt, reopen
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                # Too many failures, open circuit
                self.state = CircuitState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.is_open():
            raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass
```

#### Step 4.2: Implement Exponential Backoff
- [ ] Create `adws/adw_modules/backoff.py`
- [ ] Add jitter to prevent thundering herd
- [ ] Support configurable max delay

**Code to Implement:**
```python
# adws/adw_modules/backoff.py
"""Exponential backoff with jitter."""

import random
import time

class ExponentialBackoff:
    """Exponential backoff calculator with jitter."""

    def __init__(self, base: float = 1.0, max_delay: float = 60.0, jitter: bool = True):
        """Initialize backoff calculator.

        Args:
            base: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter to prevent thundering herd
        """
        self.base = base
        self.max_delay = max_delay
        self.jitter = jitter
        self.attempt = 0

    def next(self) -> float:
        """Get next backoff delay.

        Returns:
            Delay in seconds
        """
        delay = min(self.base * (2 ** self.attempt), self.max_delay)

        if self.jitter:
            # Add up to 25% jitter
            jitter_range = delay * 0.25
            delay += random.uniform(0, jitter_range)

        self.attempt += 1
        return delay

    def reset(self):
        """Reset backoff state."""
        self.attempt = 0
```

#### Step 4.3: Implement Dead Letter Queue
- [ ] Create `adws/adw_modules/dead_letter_queue.py`
- [ ] Store failed workflows for manual retry
- [ ] Add API to inspect and reprocess failures

**Code to Implement:**
```python
# adws/adw_modules/dead_letter_queue.py
"""Dead letter queue for failed workflows."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class DeadLetterQueue:
    """Queue for workflows that failed after all retries."""

    def __init__(self, queue_dir: str = None):
        """Initialize dead letter queue.

        Args:
            queue_dir: Directory to store failed workflows
        """
        if queue_dir is None:
            project_root = Path(__file__).parent.parent.parent
            queue_dir = project_root / "agents" / "dead_letter_queue"

        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def add(self, adw_id: str, request: Dict[str, Any], error: str):
        """Add failed workflow to queue.

        Args:
            adw_id: Workflow identifier
            request: Request that failed
            error: Error message
        """
        entry = {
            "adw_id": adw_id,
            "request": request,
            "error": error,
            "failed_at": datetime.utcnow().isoformat(),
        }

        file_path = self.queue_dir / f"{adw_id}.json"
        with open(file_path, "w") as f:
            json.dump(entry, f, indent=2)

    def list(self) -> List[Dict[str, Any]]:
        """List all failed workflows.

        Returns:
            List of failed workflow entries
        """
        entries = []
        for file_path in self.queue_dir.glob("*.json"):
            with open(file_path) as f:
                entries.append(json.load(f))

        return sorted(entries, key=lambda x: x["failed_at"], reverse=True)

    def remove(self, adw_id: str):
        """Remove workflow from queue.

        Args:
            adw_id: Workflow identifier
        """
        file_path = self.queue_dir / f"{adw_id}.json"
        if file_path.exists():
            file_path.unlink()
```

#### Step 4.4: Enhanced Retry Logic
- [ ] Update `adws/adw_modules/agent.py` with all recovery components
- [ ] Add retry strategy configuration
- [ ] Implement idempotency checks

**Code to Implement:**
```python
# adws/adw_modules/agent.py (updated retry logic)
"""Enhanced retry logic with circuit breaker and exponential backoff."""

from adw_modules.circuit_breaker import CircuitBreaker, CircuitBreakerError
from adw_modules.backoff import ExponentialBackoff
from adw_modules.dead_letter_queue import DeadLetterQueue

# Global instances
_circuit_breakers = {}
_dead_letter_queue = DeadLetterQueue()

def get_circuit_breaker(service: str) -> CircuitBreaker:
    """Get or create circuit breaker for service."""
    if service not in _circuit_breakers:
        _circuit_breakers[service] = CircuitBreaker()
    return _circuit_breakers[service]

def prompt_claude_code_with_retry(
    request: AgentPromptRequest,
    max_retries: int = 3,
) -> AgentPromptResponse:
    """Execute Claude Code with advanced retry logic.

    Features:
    - Exponential backoff with jitter
    - Circuit breaker to stop retrying if service is down
    - Dead letter queue for permanently failed requests

    Args:
        request: The prompt request configuration
        max_retries: Maximum number of retry attempts

    Returns:
        AgentPromptResponse with output and success status
    """
    circuit_breaker = get_circuit_breaker("claude_code")
    backoff = ExponentialBackoff(base=1.0, max_delay=60.0)

    for attempt in range(max_retries + 1):
        # Check circuit breaker
        if circuit_breaker.is_open():
            error_msg = "Claude Code service is unavailable (circuit breaker open)"
            _dead_letter_queue.add(
                request.adw_id,
                request.model_dump(),
                error_msg
            )
            return AgentPromptResponse(
                output=error_msg,
                success=False,
                session_id=None
            )

        try:
            # Execute request
            response = circuit_breaker.call(prompt_claude_code, request)

            if response.success:
                return response

            # Failed but didn't raise exception
            if attempt < max_retries:
                delay = backoff.next()
                time.sleep(delay)
                continue
            else:
                # Max retries exceeded
                _dead_letter_queue.add(
                    request.adw_id,
                    request.model_dump(),
                    response.output
                )
                return response

        except CircuitBreakerError as e:
            # Circuit opened during retry
            _dead_letter_queue.add(
                request.adw_id,
                request.model_dump(),
                str(e)
            )
            return AgentPromptResponse(
                output=str(e),
                success=False,
                session_id=None
            )

        except Exception as e:
            if attempt < max_retries:
                delay = backoff.next()
                time.sleep(delay)
                continue
            else:
                # Max retries exceeded
                error_msg = f"Failed after {max_retries} retries: {e}"
                _dead_letter_queue.add(
                    request.adw_id,
                    request.model_dump(),
                    error_msg
                )
                return AgentPromptResponse(
                    output=error_msg,
                    success=False,
                    session_id=None
                )

    # Should not reach here
    return AgentPromptResponse(
        output="Unexpected error in retry logic",
        success=False,
        session_id=None
    )
```

#### Step 4.5: Testing & Validation
- [ ] Test circuit breaker opens after failures
- [ ] Verify exponential backoff timing
- [ ] Test dead letter queue recovery
- [ ] Load test with simulated failures

**Success Criteria:**
- ✓ Circuit breaker prevents retry storms
- ✓ Backoff prevents thundering herd
- ✓ Failed workflows preserved in DLQ
- ✓ Manual recovery possible from DLQ

---

# Issue #5: Enhanced Observability (MEDIUM PRIORITY)

## Current State Assessment

**What Already Exists (.claude/hooks/):**
- ✅ Session-level logging in `logs/{session_id}/`
- ✅ JSON-formatted logs (notification.json, post_tool_use.json, user_prompt_submit.json)
- ✅ Claude Code session tracking with session_id
- ✅ Basic hook system for capturing tool usage

**What's MISSING (ADW-Specific):**
- ❌ Workflow-level correlation (ADW ID linking across phases)
- ❌ Cross-phase distributed tracing (plan → build → test → review → document)
- ❌ Workflow metrics (success rate by workflow type, cost per issue, duration by phase)
- ❌ Structured logging at workflow orchestration layer
- ❌ Real-time dashboards for ADW workflows
- ❌ Correlation between Claude sessions and ADW workflows

## Problem Description

**Current Hook System Scope:**
- Logs individual Claude Code CLI sessions
- No visibility into ADW workflow execution
- Cannot trace a workflow across multiple phases
- No metrics on ADW-level performance (success rates, costs, durations)

**Example Gap:**
```
ADW Workflow: Issue #123 → adw_sdlc_iso.py
  Phase 1: Planning → Claude session abc123
  Phase 2: Build → Claude session def456
  Phase 3: Test → Claude session ghi789

Current: 3 separate session logs (no linking)
Needed: Single workflow trace linking all 3 sessions
```

**What We Need:**
- Workflow-level structured logging (adw_id as primary correlation ID)
- Distributed tracing across all 5 phases (plan, build, test, review, document)
- Real-time metrics dashboard showing ADW workflow stats
- Link Claude sessions to ADW workflows
- Aggregate cost/duration/success metrics by workflow type

## Solution: ADW-Specific Observability Layer

### Implementation Checklist

#### Step 5.0: Bridge Hook System with ADW Observability (NEW)
- [ ] Modify `adws/adw_modules/agent.py` to pass ADW ID to Claude Code
- [ ] Update hook system to extract and log ADW ID from session metadata
- [ ] Create workflow trace file linking Claude sessions to ADW workflows
- [ ] Add ADW context to existing hook logs

**Code to Implement:**
```python
# adws/adw_modules/agent.py (updated execute_template)
def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute template with ADW context for hook system."""

    # Add ADW metadata to prompt for hooks to capture
    enriched_prompt = f"""
ADW_CONTEXT:
  adw_id: {request.adw_id}
  agent_name: {request.agent_name}
  slash_command: {request.slash_command}
END_ADW_CONTEXT

{request.slash_command} {' '.join(request.args)}
"""

    # Execute with enriched context
    # ... rest of implementation
```

**Hook Integration:**
```python
# .claude/hooks/post_tool_use.py (updated to capture ADW context)
def extract_adw_context(input_data):
    """Extract ADW context from Claude Code session."""
    # Parse ADW_CONTEXT from messages if present
    messages = input_data.get('messages', [])
    for msg in messages:
        content = msg.get('content', '')
        if 'ADW_CONTEXT:' in content:
            # Extract adw_id and link to session
            # Save to workflow trace file
            pass

def main():
    input_data = json.load(sys.stdin)
    session_id = input_data.get('session_id', 'unknown')

    # Extract and log ADW context
    adw_context = extract_adw_context(input_data)

    # If ADW context found, also log to workflow trace
    if adw_context:
        link_session_to_workflow(session_id, adw_context)

    # ... rest of hook logic
```

**Workflow Trace File:**
```json
// agents/{adw_id}/workflow_trace.json
{
  "adw_id": "a1b2c3d4",
  "issue_number": "123",
  "workflow": "adw_sdlc_iso",
  "phases": [
    {
      "phase": "planning",
      "agent_name": "planner",
      "session_id": "abc123",
      "start_time": "2025-10-05T12:00:00Z",
      "end_time": "2025-10-05T12:05:00Z",
      "duration_ms": 300000,
      "cost_usd": 0.45,
      "success": true
    },
    {
      "phase": "implementation",
      "agent_name": "implementor",
      "session_id": "def456",
      "start_time": "2025-10-05T12:05:00Z",
      "end_time": "2025-10-05T12:15:00Z",
      "duration_ms": 600000,
      "cost_usd": 1.23,
      "success": true
    }
  ],
  "total_duration_ms": 900000,
  "total_cost_usd": 1.68,
  "final_status": "success"
}
```

#### Step 5.1: Add Structured Logging
- [ ] Install structlog: `uv add structlog`
- [ ] Create `adws/adw_modules/logging_config.py`
- [ ] Add correlation IDs to all log statements
- [ ] Use adw_id as primary correlation field (not just session_id)

**Code to Implement:**
```python
# adws/adw_modules/logging_config.py
"""Structured logging configuration."""

import structlog
import logging
from typing import Optional

def configure_logging(adw_id: Optional[str] = None):
    """Configure structured logging.

    Args:
        adw_id: Workflow ID to include in all logs
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set log level
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

def get_logger(name: str, adw_id: Optional[str] = None):
    """Get structured logger with context.

    Args:
        name: Logger name
        adw_id: Workflow ID for context

    Returns:
        Configured structlog logger
    """
    logger = structlog.get_logger(name)

    if adw_id:
        logger = logger.bind(adw_id=adw_id)

    return logger
```

#### Step 5.2: Add OpenTelemetry Tracing
- [ ] Install OpenTelemetry: `uv add opentelemetry-api opentelemetry-sdk`
- [ ] Create `adws/adw_modules/tracing.py`
- [ ] Add spans to all workflow phases

**Code to Implement:**
```python
# adws/adw_modules/tracing.py
"""OpenTelemetry tracing for ADW workflows."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

def configure_tracing(service_name: str = "adw"):
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Service name for traces
    """
    resource = Resource(attributes={
        "service.name": service_name
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

def get_tracer(name: str):
    """Get tracer instance.

    Args:
        name: Tracer name

    Returns:
        OpenTelemetry tracer
    """
    return trace.get_tracer(name)
```

#### Step 5.3: Update Workflows with Tracing
- [ ] Add tracing to all workflow phases
- [ ] Include metrics in spans (duration, cost, success)
- [ ] Link spans across phases

**Example:**
```python
# Example: adws/adw_plan.py (with tracing)
from adw_modules.tracing import get_tracer
from adw_modules.logging_config import get_logger

tracer = get_tracer(__name__)
logger = get_logger(__name__, adw_id=adw_id)

with tracer.start_as_current_span("workflow.plan") as span:
    span.set_attribute("issue_number", issue_number)
    span.set_attribute("adw_id", adw_id)

    logger.info("workflow_started", phase="plan")

    # Execute planning
    response = execute_template(request)

    span.set_attribute("success", response.success)
    span.set_attribute("cost_usd", response.cost)

    logger.info("workflow_completed", phase="plan", success=response.success)
```

#### Step 5.4: Metrics Dashboard
- [ ] Create `adws/adw_triggers/metrics_api.py`
- [ ] Expose Prometheus metrics
- [ ] Add Grafana dashboard configuration

**Success Criteria:**
- ✓ All logs in JSON format with correlation IDs
- ✓ Traces link all phases of a workflow
- ✓ Metrics available via Prometheus endpoint
- ✓ Can debug failures using correlation ID

---

# Issue #6: Feedback Loop System (MEDIUM PRIORITY)

## Problem Description

**Current:** KPIs tracked but not used for optimization
**Missing:**
- A/B testing of workflows
- Automatic workflow selection based on success rates
- Learning from failures

## Solution: Workflow Optimizer with A/B Testing

### Implementation Checklist

#### Step 6.1: Create Workflow Optimizer
- [ ] Create `adws/adw_modules/workflow_optimizer.py`
- [ ] Implement success rate tracking
- [ ] Add workflow recommendation system

**Code to Implement:**
```python
# adws/adw_modules/workflow_optimizer.py
"""Workflow optimizer using historical KPIs."""

import json
from pathlib import Path
from typing import Optional, List, Dict
from collections import defaultdict

class WorkflowOptimizer:
    """Optimizes workflow selection based on historical performance."""

    def __init__(self, kpi_file: Optional[str] = None):
        """Initialize optimizer.

        Args:
            kpi_file: Path to KPI tracking file
        """
        if kpi_file is None:
            project_root = Path(__file__).parent.parent.parent
            kpi_file = project_root / "app_docs" / "agentic_kpis.json"

        self.kpi_file = Path(kpi_file)
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict:
        """Load KPI statistics."""
        if not self.kpi_file.exists():
            return {"workflows": defaultdict(lambda: {"success": 0, "failure": 0, "avg_attempts": 0})}

        with open(self.kpi_file) as f:
            return json.load(f)

    def recommend_workflow(self, issue_class: str) -> str:
        """Recommend best workflow for issue class.

        Args:
            issue_class: Issue classification (/bug, /feature, /chore)

        Returns:
            Recommended workflow name
        """
        # Get workflows for this issue class
        workflows = self.stats["workflows"].get(issue_class, {})

        if not workflows:
            # No history, use default
            return "adw_sdlc_iso"

        # Calculate success rates
        best_workflow = None
        best_rate = 0.0

        for workflow, metrics in workflows.items():
            total = metrics["success"] + metrics["failure"]
            if total > 0:
                rate = metrics["success"] / total
                if rate > best_rate:
                    best_rate = rate
                    best_workflow = workflow

        return best_workflow or "adw_sdlc_iso"

    def record_outcome(self, workflow: str, issue_class: str, success: bool, attempts: int):
        """Record workflow outcome.

        Args:
            workflow: Workflow name
            issue_class: Issue classification
            success: Whether workflow succeeded
            attempts: Number of attempts needed
        """
        if issue_class not in self.stats["workflows"]:
            self.stats["workflows"][issue_class] = {}

        if workflow not in self.stats["workflows"][issue_class]:
            self.stats["workflows"][issue_class][workflow] = {
                "success": 0,
                "failure": 0,
                "total_attempts": 0,
                "avg_attempts": 0
            }

        metrics = self.stats["workflows"][issue_class][workflow]

        if success:
            metrics["success"] += 1
        else:
            metrics["failure"] += 1

        metrics["total_attempts"] += attempts
        total = metrics["success"] + metrics["failure"]
        metrics["avg_attempts"] = metrics["total_attempts"] / total

        # Save updated stats
        with open(self.kpi_file, "w") as f:
            json.dump(self.stats, f, indent=2)
```

#### Step 6.2: A/B Testing Framework
- [ ] Create `adws/adw_modules/ab_testing.py`
- [ ] Implement variant selection with exploration/exploitation
- [ ] Track experiment results

**Code to Implement:**
```python
# adws/adw_modules/ab_testing.py
"""A/B testing framework for workflows."""

import random
from typing import List, Dict

class ABTester:
    """A/B testing framework with epsilon-greedy strategy."""

    def __init__(self, epsilon: float = 0.1):
        """Initialize A/B tester.

        Args:
            epsilon: Exploration rate (0.0 = exploit only, 1.0 = explore only)
        """
        self.epsilon = epsilon
        self.experiments: Dict[str, List[str]] = {}

    def should_experiment(self) -> bool:
        """Decide whether to run experiment variant.

        Returns:
            True if should use experimental variant
        """
        return random.random() < self.epsilon

    def add_experiment(self, name: str, variants: List[str]):
        """Add new A/B test experiment.

        Args:
            name: Experiment name
            variants: List of workflow variants to test
        """
        self.experiments[name] = variants

    def pick_variant(self, experiment: str = "default") -> str:
        """Pick random variant from experiment.

        Args:
            experiment: Experiment name

        Returns:
            Selected variant
        """
        variants = self.experiments.get(experiment, ["adw_sdlc_iso"])
        return random.choice(variants)
```

#### Step 6.3: Integration with Workflows
- [ ] Update trigger scripts to use optimizer
- [ ] Add automatic workflow selection
- [ ] Track experiment results

**Success Criteria:**
- ✓ Workflow selection based on historical success rates
- ✓ A/B tests running with configurable exploration rate
- ✓ KPI dashboard shows optimization results

---

# Issue #7: Declarative Workflows (STRATEGIC)

## Problem Description

**Current:** Imperative Python scripts
**Better:** State machine definitions (YAML/JSON)

**Benefits:**
- Easier to visualize workflow graphs
- Simpler to A/B test variants
- Version control friendly
- Non-programmers can edit workflows

## Solution: State Machine Engine

### Implementation Checklist

#### Step 7.1: Define Workflow Schema
- [ ] Create `adws/workflows/schema.json` (JSON Schema for workflows)
- [ ] Create example workflow: `adws/workflows/sdlc.yaml`

**Example:**
```yaml
# adws/workflows/sdlc.yaml
name: sdlc
description: Complete SDLC workflow

states:
  planning:
    command: /classify_issue
    on_success: implementation
    on_failure: dead_letter

  implementation:
    command: /implement
    args: ["${plan_file}"]
    on_success: testing
    on_failure: retry_implementation
    max_retries: 3

  retry_implementation:
    command: /patch
    on_success: testing
    on_failure: dead_letter

  testing:
    command: /test
    on_success: review
    on_failure: fix_tests

  fix_tests:
    command: /resolve_failed_test
    on_success: testing
    on_failure: dead_letter
    max_retries: 5

  review:
    command: /review
    on_success: documentation
    on_failure: dead_letter

  documentation:
    command: /document
    on_success: complete
    on_failure: complete  # Optional step

  complete:
    terminal: true

  dead_letter:
    terminal: true
    action: record_failure
```

#### Step 7.2: Create State Machine Engine
- [ ] Create `adws/adw_modules/state_machine.py`
- [ ] Implement workflow parser
- [ ] Add execution engine

**Success Criteria:**
- ✓ Workflows defined in YAML
- ✓ State machine engine executes workflows
- ✓ Visualize workflows as graphs

---

# Issue #8: Adapter Pattern (STRATEGIC)

## Problem Description

**Current:** Tight coupling to GitHub, Claude Code
**Better:** Abstract interfaces for swappable backends

## Solution: Adapter Pattern

### Implementation Checklist

#### Step 8.1: Define Interfaces
- [ ] Create `adws/adw_modules/interfaces/issue_tracker.py`
- [ ] Create `adws/adw_modules/interfaces/git_provider.py`

**Code Example:**
```python
# adws/adw_modules/interfaces/issue_tracker.py
from typing import Protocol
from adw_modules.data_types import GitHubIssue

class IssueTracker(Protocol):
    """Interface for issue tracking systems."""

    def get_issue(self, number: int) -> GitHubIssue:
        """Get issue by number."""
        ...

    def post_comment(self, number: int, body: str):
        """Post comment on issue."""
        ...

    def close_issue(self, number: int):
        """Close issue."""
        ...
```

#### Step 8.2: Implement Adapters
- [ ] Create GitHub adapter (current implementation)
- [ ] Create Jira adapter
- [ ] Create Linear adapter

**Success Criteria:**
- ✓ Can swap issue trackers via configuration
- ✓ Multi-platform support (GitHub, Jira, Linear)

---

# Issue #9: Security Hardening (STRATEGIC)

## Problem Description

**Missing:**
- Input validation (issue bodies can be malicious)
- Rate limiting on webhooks
- Audit logging
- Secrets rotation
- Code execution sandboxing

## Solution: Security Framework

### Implementation Checklist

#### Step 9.1: Input Validation
- [ ] Create `adws/adw_modules/validators.py`
- [ ] Sanitize issue bodies
- [ ] Limit request sizes

#### Step 9.2: Audit Logging
- [ ] Create `adws/adw_modules/audit_log.py`
- [ ] Log all workflow triggers with user info
- [ ] Track who/what/when

#### Step 9.3: Secrets Management
- [ ] Implement secrets rotation schedule
- [ ] Add secrets scanner to prevent commits
- [ ] Use environment-based secrets only

**Success Criteria:**
- ✓ No malicious input can execute arbitrary code
- ✓ All actions audited
- ✓ Secrets rotated automatically

---

## Success Metrics

### Phase 1 (Priority 1-2) - Week 4
- [ ] Zero state corruption under 20 parallel workflows
- [ ] Can swap execution engines without code changes
- [ ] System stable under resource pressure
- [ ] No retry storms (circuit breaker working)
- [ ] Failed workflows preserved in DLQ

### Phase 2 (Priority 3) - Month 2
- [ ] All logs structured with correlation IDs
- [ ] Distributed traces for full workflows
- [ ] Workflow selection based on success rates
- [ ] A/B testing shows 10%+ success rate improvement

### Phase 3 (Priority 4) - Month 3
- [ ] 50%+ workflows defined in YAML
- [ ] Multi-platform support (GitHub + Jira)
- [ ] Zero security incidents
- [ ] Complete audit trail for compliance

---

## Implementation Timeline

### Week 1-2: Critical Fixes
- Day 1-3: SQLite state management
- Day 4-5: Migration script and testing
- Day 6-8: Execution engine abstraction
- Day 9-10: Testing and validation

### Week 3-4: High Priority
- Day 1-3: Resource management
- Day 4-5: Circuit breaker and backoff
- Day 6-7: Dead letter queue
- Day 8-10: Integration testing

### Month 2: Medium Priority
- Week 1: Structured logging + OpenTelemetry
- Week 2: Metrics and monitoring
- Week 3: Workflow optimizer
- Week 4: A/B testing framework

### Month 3: Strategic Improvements
- Week 1: Declarative workflows (YAML)
- Week 2: Adapter pattern
- Week 3: Security hardening
- Week 4: Documentation and final testing

---

## Rollout Strategy

### Phase 1: Parallel Testing
- [ ] Run new system alongside old system
- [ ] Compare results for 1 week
- [ ] Verify no regressions

### Phase 2: Gradual Migration
- [ ] Migrate 10% of workflows to new system
- [ ] Monitor for 1 week
- [ ] Increase to 50% if stable
- [ ] Full migration after 2 weeks

### Phase 3: Monitoring
- [ ] Track KPIs daily for 1 month
- [ ] Compare before/after metrics
- [ ] Document improvements

---

## Emergency Rollback Plan

If critical issues arise:

1. **Revert to File-Based State:**
   ```python
   # In state.py
   state = ADWState(adw_id, use_db=False)
   ```

2. **Revert to Direct Claude Code:**
   ```python
   # In agent.py
   response = prompt_claude_code(request)  # Skip engine factory
   ```

3. **Restore from Backup:**
   ```bash
   # Restore state database
   cp agents/adw_state.db.backup agents/adw_state.db
   ```

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize** based on current pain points
3. **Start with Issue #1** (state management)
4. **Track progress** using this checklist
5. **Update timeline** as needed

---

## Questions for Discussion

- [ ] What is acceptable downtime for migration?
- [ ] Should we prioritize cost optimization over speed?
- [ ] Do we need multi-region support?
- [ ] What compliance requirements exist (SOC2, GDPR)?
- [ ] Should we build or buy monitoring solution?

---

**Document Owner:** AI Developer Workflow Team
**Last Updated:** 2025-10-05
**Next Review:** After Phase 1 completion
