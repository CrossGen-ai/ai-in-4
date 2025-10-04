# Template Cleanup Plan
**Generated:** 2025-10-04
**Status:** Action Required Before Template Use
**Completion:** ~85%

---

## Executive Summary

Your infrastructure is **very close** to being a perfect generic template. The core architecture is solid, environment configuration is excellent, and the tech stack is properly implemented. However, there are **3 critical issues** that must be resolved before this can be used as a template for future projects.

**Time to Fix:** 15-30 minutes
**Blocking Issues:** 3 critical, 2 important
**Risk Level:** High (template will fail on first use without fixes)

---

## ❌ CRITICAL ISSUES (Must Fix)

### 1. README.md is Application-Specific

**Location:** `/README.md`

**Problem:**
- Entire README describes "Natural Language SQL Interface" application
- Contains SQL-specific features, API endpoints, and security details
- Mentions drag-and-drop file uploads, natural language queries
- Documents SQL injection protection (lines 133-177)
- Lists SQL-specific API endpoints (lines 123-130)

**Why Critical:**
Any developer cloning this template will see documentation for a completely different application. This breaks the entire premise of a generic template.

**Resolution:**

Delete current README.md and create a new generic one:


**New README.md Content:**

```markdown
# FastAPI + React TypeScript Template

A production-ready full-stack template with React + TypeScript + Tailwind v4 + Shadcn UI on the frontend and FastAPI + Python on the backend.

## Features

- ⚡ **Frontend**: React 18 + TypeScript + Vite 7 + Tailwind CSS v4 + Shadcn UI
- 🚀 **Backend**: FastAPI + Python 3.10+ + uvicorn
- 🧪 **Testing**: Vitest (frontend) + Pytest (backend)
- 🔧 **Dev Tools**: ESLint, Ruff, Hot Reload
- 📦 **Package Management**: npm (frontend) + uv (backend)
- 🎯 **ADW Compatible**: Works with AI Developer Workflow automation (triggered through hooks or uv in the terminal)
- 🌍 **Environment-Based Config**: All ports and settings via .env files

## Tech Stack

### Frontend
- React 18.3+
- TypeScript 5.9+
- Vite 7+ (build tool)
- Tailwind CSS v4 (styling)
- Shadcn UI (component library)
- Vitest (testing)

### Backend
- FastAPI 0.115+
- Python 3.10+
- uvicorn (ASGI server)
- Pydantic v2 (validation)
- pytest (testing)
- uv (package manager)

## Prerequisites

- Python 3.10+
- Node.js 18+
- uv (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- npm or your preferred package manager

## Quick Start

### 1. Install Dependencies

```bash
# Backend
cd app/server
uv sync --all-extras

# Frontend
cd app/client
npm install
```

### 2. Environment Configuration

**Root environment (for scripts):**
```bash
cp .sample.env .env
# Edit .env: Set CLIENT_PORT, SERVER_PORT, and ADW variables if using automation
```

**Server environment:**
```bash
cd app/server
cp .env.sample .env
# Edit .env: Set SERVER_PORT, ALLOWED_ORIGINS, and add your API keys
```

**Client environment:**
```bash
cd app/client
cp .env.sample .env.local
# Edit .env.local: Set VITE_PORT and VITE_API_URL
```

**Important:** Ensure port values match across all three .env files!

### 3. Start Development Servers

**Option 1: Use start script (recommended)**
```bash
./scripts/start.sh
```

**Option 2: Manual start**
```bash
# Terminal 1: Backend
cd app/server
uv run python server.py

# Terminal 2: Frontend
cd app/client
npm run dev
```

### 4. Verify Setup

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
.
├── app/
│   ├── client/              # React + TypeScript frontend
│   │   ├── src/
│   │   │   ├── components/  # React components
│   │   │   │   ├── ui/      # Shadcn UI components
│   │   │   │   └── layout/  # Layout components
│   │   │   ├── lib/         # Utilities and API client
│   │   │   ├── hooks/       # Custom React hooks
│   │   │   ├── pages/       # Page components
│   │   │   └── types/       # TypeScript types
│   │   └── ...
│   │
│   └── server/              # FastAPI backend
│       ├── api/             # API routes
│       │   └── routes/      # Route modules
│       ├── core/            # Core configuration
│       ├── models/          # Pydantic models
│       ├── services/        # Business logic
│       ├── db/              # Database layer
│       └── tests/           # Backend tests
│
├── .claude/                 # Claude Code automation
│   └── commands/            # ADW slash commands
├── scripts/                 # Utility scripts
├── .sample.env              # Root environment template
└── INFRASTRUCTURE_PLAN.md   # Detailed infrastructure documentation
```

## Development

### Backend Commands
```bash
cd app/server
uv run python server.py      # Start server with hot reload
uv run pytest -v             # Run tests
uv run ruff check .          # Lint code
uv add <package>             # Add dependency
```

### Frontend Commands
```bash
cd app/client
npm run dev                  # Start dev server
npm run build                # Build for production
npm run type-check           # TypeScript type checking
npm test                     # Run tests
npm run lint                 # Lint code
```

### Running Tests

```bash
# Frontend tests
cd app/client && npm test

# Backend tests
cd app/server && uv run pytest -v

# Type checking
cd app/client && npm run type-check
```

## Adding Features

### 1. Add New API Endpoint

Create a new route file:
```python
# app/server/api/routes/example.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example_endpoint():
    return {"message": "Hello from example endpoint"}
```

Register in main.py:
```python
# app/server/main.py
from api.routes import example

app.include_router(example.router, prefix="/api", tags=["example"])
```

### 2. Add New Frontend Component

Create component in appropriate directory:
```typescript
// app/client/src/components/features/Example.tsx
export function Example() {
  return <div>Example Component</div>
}
```

### 3. Add Environment Variables

Add to `.env.sample` files, then update:
- `app/server/core/config.py` for backend vars
- Access with `import.meta.env.VITE_*` for frontend vars

## Environment Configuration

This template uses environment-based configuration for maximum flexibility:

- **Root `.env`**: Used by scripts (start.sh, stop_apps.sh) and ADW workflows
- **Client `.env.local`**: Frontend configuration (must use VITE_ prefix)
- **Server `.env`**: Backend configuration (loaded by pydantic-settings)

### Port Configuration

Default ports:
- Frontend: 5173 (configurable via VITE_PORT)
- Backend: 8000 (configurable via SERVER_PORT)

To change ports:
1. Update root `.env`: CLIENT_PORT and SERVER_PORT
2. Update `app/server/.env`: SERVER_PORT and ALLOWED_ORIGINS
3. Update `app/client/.env.local`: VITE_PORT and VITE_API_URL

## AI Developer Workflow (ADW)

This template is designed to work with the ADW automation system in `.claude/commands/`.

The ADW system provides slash commands for:
- `/feature` - Implement new features
- `/bug` - Fix bugs
- `/chore` - Maintenance tasks
- `/test` - Run comprehensive test suite
- And more...

See [ADW README](adws/README.md) for detailed setup and usage.

## Troubleshooting

### Port Already in Use

If ports 5173 or 8000 are in use:

```bash
# Option 1: Kill processes on ports
lsof -ti:5173 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Option 2: Change ports in .env files
# Edit .env, app/server/.env, and app/client/.env.local
# Update CLIENT_PORT, SERVER_PORT, VITE_PORT, VITE_API_URL, ALLOWED_ORIGINS
```

### CORS Errors

Ensure `ALLOWED_ORIGINS` in `app/server/.env` includes your frontend URL:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Module Not Found Errors

```bash
# Backend
cd app/server && uv sync --all-extras

# Frontend
cd app/client && rm -rf node_modules && npm install
```

### Tests Failing

```bash
# Ensure dependencies are installed
cd app/server && uv sync --all-extras
cd app/client && npm install

# Run tests with verbose output
cd app/server && uv run pytest -v
cd app/client && npm test
```

## Production Deployment

This template is development-ready. For production:

1. Update CORS settings in `app/server/.env`
2. Set `SERVER_RELOAD=false` for production
3. Build frontend: `cd app/client && npm run build`
4. Serve frontend build with nginx or similar
5. Run backend with production ASGI server (uvicorn with workers)
6. Use environment variables for all secrets
7. Enable HTTPS/SSL

## Documentation

- [Infrastructure Plan](INFRASTRUCTURE_PLAN.md) - Comprehensive infrastructure documentation
- [ADW System](adws/README.md) - AI Developer Workflow automation

## License

MIT (or your preferred license)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and type checking
5. Submit a pull request
```

**Verification:**
- [ ] README describes generic template, not SQL app
- [ ] No application-specific features mentioned
- [ ] Setup instructions are generic and complete
- [ ] Port configuration is explained
- [ ] Troubleshooting section included

---

### 2. Application-Specific Test Files Must Be Removed

**Location:** `app/server/tests/`

**Problem:**
These test files reference modules that were correctly removed in Phase 2.5 (file_processor, sql_processor, llm_processor, sql_security). Keeping them will cause test failures and break the ADW `/test` command.

**Files to Delete:**

```bash
# Delete application-specific test files
rm app/server/tests/core/test_file_processor.py
rm app/server/tests/core/test_llm_processor.py
rm app/server/tests/core/test_sql_processor.py
rm app/server/tests/test_sql_injection.py

# Delete application-specific test directory
rm -rf app/server/tests/core/

# Delete application-specific test assets
rm -rf app/server/tests/assets/
```

**Why Critical:**
- Line 3 of `test_file_processor.py`: `from core.file_processor import convert_csv_to_sqlite...`
- These modules don't exist (correctly removed)
- The `/test` command will fail immediately
- Breaks ADW automation system

**What to Keep:**
- ✅ `app/server/tests/__init__.py`
- ✅ `app/server/tests/test_health.py` (generic health check test)

**Resolution Commands:**

```bash
cd /Users/crossgenai/Projects/ai-in-4

# Remove application-specific tests
rm -rf app/server/tests/core/
rm -rf app/server/tests/assets/
rm app/server/tests/test_sql_injection.py

# Verify only generic tests remain
ls -la app/server/tests/
# Should show: __init__.py, test_health.py only
```

**Verification:**
```bash
# Test should pass after cleanup
cd app/server && uv run pytest -v
# Should show: test_health.py::test_health_check PASSED
```

---

### 3. Application-Specific Comment in Core Module

**Location:** `app/server/core/__init__.py:1`

**Current Content:**
```python
# Core module for Natural Language SQL Interface
```

**Problem:**
References the SQL application specifically.

**Resolution:**

```bash
# Option 1: Use Edit command
# Edit the file to replace the comment
```

**New Content:**
```python
# Core module for application configuration and utilities
```

**Verification:**
```bash
cat app/server/core/__init__.py
# Should show: "# Core module for application configuration and utilities"
```

---

## ⚠️ IMPORTANT ISSUES (Should Fix)

### 4. Test Command Description References SQL Features

**Location:** `.claude/commands/test.md:58`

**Current Line 58:**
```
test_purpose: "Validates all backend functionality including file processing, SQL security, LLM integration, and API endpoints"
```

**Problem:**
References removed features (file processing, SQL security, LLM integration).

**Resolution:**

Replace line 58 with:
```
test_purpose: "Validates all backend functionality including API endpoints and business logic"
```

**Full Command:**
```bash
# Edit .claude/commands/test.md line 58
# Change: "Validates all backend functionality including file processing, SQL security, LLM integration, and API endpoints"
# To: "Validates all backend functionality including API endpoints and business logic"
```

---

### 5. Missing .env.local in .gitignore

**Location:** `.gitignore:3`

**Current Lines 1-3:**
```gitignore
# Environment variables
.env
app/server/.env
```

**Problem:**
Missing `app/client/.env.local` which could lead to accidentally committing frontend environment variables.

**Resolution:**

Add line 4:
```gitignore
# Environment variables
.env
app/server/.env
app/client/.env.local
```

**Verification:**
```bash
cat .gitignore | head -5
# Should show all three env files listed
```

---

## 📋 ADDITIONAL RECOMMENDATIONS

### 6. Remove Committed .env File (If Exists)

**Check:**
```bash
git ls-files .env
```

**If file is tracked:**
```bash
git rm .env
git commit -m "chore: Remove committed .env file from repository"
```

**Add to .gitignore (already done):**
```gitignore
.env
```

---

### 7. Add Root package.json for Convenience (Optional)

**Location:** Create `/package.json`

**Content:**
```json
{
  "name": "fastapi-react-template",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "start": "./scripts/start.sh",
    "stop": "./scripts/stop_apps.sh",
    "install": "cd app/server && uv sync --all-extras && cd ../client && npm install",
    "test": "cd app/server && uv run pytest -v && cd ../client && npm test",
    "lint": "cd app/server && uv run ruff check . && cd ../client && npm run lint"
  },
  "description": "Full-stack template with FastAPI + React TypeScript"
}
```

**Benefits:**
- Convenient shortcuts: `npm start`, `npm test` from root
- Consistent with modern project conventions
- Easier for new developers

---

### 8. Document Port Conflict Resolution

**Already included in new README.md above** ✅

---

### 9. Create Example Feature Template (Optional)

**Location:** Create `app/server/api/routes/example.py.disabled`

**Content:**
```python
# Example feature route - Rename to .py and uncomment to use
# This serves as a template for adding new features

# from fastapi import APIRouter, HTTPException
# from typing import List
# from models.schemas import ExampleRequest, ExampleResponse

# router = APIRouter()

# @router.get("/example")
# async def get_example():
#     """
#     Example GET endpoint
#     """
#     return {"message": "Example endpoint"}

# @router.post("/example")
# async def create_example(request: ExampleRequest):
#     """
#     Example POST endpoint with request validation
#     """
#     return ExampleResponse(
#         id=1,
#         message=f"Received: {request.name}"
#     )

# Then register in main.py:
# from api.routes import example
# app.include_router(example.router, prefix="/api", tags=["example"])
```

**Benefits:**
- Clear pattern for adding features
- Shows best practices (validation, types, docs)
- Self-documenting

---

### 10. Add Health Check to Frontend (Optional)

**Location:** Create `app/client/src/hooks/useHealth.ts`

**Content:**
```typescript
import { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'

export function useHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const result = await api.healthCheck()
        setIsHealthy(result.status === 'healthy')
      } catch {
        setIsHealthy(false)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  return { isHealthy, loading }
}
```

**Benefits:**
- Shows integration pattern
- Useful for production monitoring
- Example custom hook

---

## 🎯 EXECUTION PLAN

### Phase 1: Critical Fixes (Required - 15 minutes)

```bash
cd /Users/crossgenai/Projects/ai-in-4

# 1. Backup current README
mv README.md README.old.md

# 2. Create new generic README
# (Use content from Critical Issue #1 above)

# 3. Remove application-specific test files
rm -rf app/server/tests/core/
rm -rf app/server/tests/assets/
rm app/server/tests/test_sql_injection.py

# 4. Fix core/__init__.py comment
# Edit app/server/core/__init__.py line 1
# Change to: "# Core module for application configuration and utilities"

# 5. Verify tests pass
cd app/server && uv run pytest -v
cd ../client && npm test

# 6. Commit changes
git add .
git commit -m "Template cleanup: Remove application-specific code and docs"
```

---

### Phase 2: Important Fixes (Recommended - 5 minutes)

```bash
# 1. Update test.md description
# Edit .claude/commands/test.md line 58

# 2. Add .env.local to .gitignore
# Edit .gitignore line 4

# 3. Remove committed .env if tracked
git ls-files .env && git rm .env

# 4. Commit
git add .
git commit -m "Template cleanup: Update test descriptions and gitignore"
```

---

### Phase 3: Optional Enhancements (10 minutes)

```bash
# 1. Add root package.json (see recommendation #7)

# 2. Add example feature template (see recommendation #9)

# 3. Add health check hook (see recommendation #10)

# 4. Commit
git add .
git commit -m "Template enhancements: Add convenience scripts and examples"
```

---

## ✅ VERIFICATION CHECKLIST

After completing all fixes, verify:

### Functionality Tests
- [ ] Backend starts without errors: `cd app/server && uv run python server.py`
- [ ] Frontend starts without errors: `cd app/client && npm run dev`
- [ ] Health endpoint works: `curl http://localhost:8000/api/health`
- [ ] Backend tests pass: `cd app/server && uv run pytest -v`
- [ ] Frontend tests pass: `cd app/client && npm test`
- [ ] TypeScript compiles: `cd app/client && npm run type-check`
- [ ] Frontend builds: `cd app/client && npm run build`

### Template Completeness
- [ ] README.md describes generic template (not SQL app)
- [ ] No application-specific code in app/server/
- [ ] No application-specific code in app/client/
- [ ] No application-specific tests
- [ ] All .env.sample files present
- [ ] No .env files committed
- [ ] All comments are generic

### ADW Compatibility
- [ ] `/test` command works
- [ ] `/start` command works
- [ ] All commands reference generic paths
- [ ] No SQL-specific references in commands

### Documentation
- [ ] README.md has setup instructions
- [ ] README.md has troubleshooting
- [ ] INFRASTRUCTURE_PLAN.md is up to date
- [ ] All environment variables documented

---

## 📊 FINAL STATUS SUMMARY

**Current State:**
- ✅ Infrastructure: 100% complete
- ✅ Frontend setup: 100% complete
- ✅ Backend setup: 100% complete
- ✅ Environment config: 100% complete
- ❌ Documentation: 0% (SQL-specific)
- ❌ Tests: 20% (4 SQL tests, 1 generic test)
- ✅ ADW compatibility: 95% (needs test cleanup)

**After Fixes:**
- ✅ Infrastructure: 100% complete
- ✅ Frontend setup: 100% complete
- ✅ Backend setup: 100% complete
- ✅ Environment config: 100% complete
- ✅ Documentation: 100% generic
- ✅ Tests: 100% generic
- ✅ ADW compatibility: 100%

**Overall Completion:**
- Current: ~85%
- After Critical Fixes: ~95%
- After All Fixes: 100%

---

## 🚀 POST-CLEANUP USAGE

Once cleanup is complete, this template can be used for any new project:

```bash
# 1. Clone/copy template
git clone <this-repo> my-new-project
cd my-new-project

# 2. Remove git history (start fresh)
rm -rf .git
git init

# 3. Update project metadata
# - Edit app/client/package.json: name, description
# - Edit app/server/pyproject.toml: name, description
# - Edit README.md: project name, description

# 4. Configure environment
cp .sample.env .env
# Edit .env with your values

cd app/server
cp .env.sample .env
# Edit .env with your API keys

cd ../client
cp .env.sample .env.local
# Edit .env.local with your settings

# 5. Install dependencies
cd app/server && uv sync --all-extras
cd ../client && npm install

# 6. Start development
./scripts/start.sh

# 7. Build your features from your PRD!
```

---

## 📝 NOTES

### What Makes This Template Excellent

1. **Environment-Based Configuration**: All ports and settings configurable via .env
2. **ADW Compatible**: Full automation system integration
3. **Modern Stack**: Latest versions of React, Vite, FastAPI, Tailwind v4
4. **Test Infrastructure**: Both frontend and backend testing configured
5. **Type Safety**: TypeScript + Pydantic for end-to-end type safety
6. **Clean Architecture**: Proper separation of concerns
7. **Production-Ready**: Build processes, linting, error handling

### What Was Successfully Removed

- ✅ SQL-specific processors (file_processor, sql_processor, sql_security)
- ✅ LLM processors
- ✅ Data models for SQL app
- ✅ Constants for SQL app
- ✅ SQL-specific API endpoints
- ✅ Database files (.db files)

### What Needs to Be Removed

- ❌ SQL-specific tests (4 test files)
- ❌ SQL-specific test assets (6 files)
- ❌ SQL-specific README.md
- ❌ SQL-specific comments

---

**Created by:** Claude Code Infrastructure Assessment
**Date:** 2025-10-04
**Version:** 1.0
**Next Review:** After completing critical fixes
