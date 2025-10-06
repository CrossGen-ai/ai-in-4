# Generic App Infrastructure Plan
## React + TypeScript + Tailwind v4 + Shadcn + FastAPI

**Created**: 2025-10-04
**Purpose**: Reusable infrastructure for future full-stack applications
**Status**: Blueprint for implementation

---

## Executive Summary

This document defines a production-ready, generic infrastructure for building modern web applications with:
- **Frontend**: React + TypeScript + Vite + Tailwind CSS v4 + Shadcn UI
- **Backend**: FastAPI + Python + uv
- **Full compatibility** with existing `.claude/commands/` automation system

This structure is designed to be saved as a template and reused for any future application built from a PRD.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Environment Configuration](#environment-configuration)
3. [Directory Structure](#directory-structure)
4. [Technology Stack](#technology-stack)
5. [Command Compatibility Matrix](#command-compatibility-matrix)
6. [Migration Steps](#migration-steps)
7. [Future Project Setup](#future-project-setup)
8. [Configuration Files](#configuration-files)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Design Principles

1. **Separation of Concerns**: Clear frontend/backend boundaries
2. **Type Safety**: End-to-end TypeScript + Pydantic types
3. **Testability**: Isolated testing for client and server
4. **Scalability**: Modular structure for growth
5. **Developer Experience**: Hot reload, fast builds, modern tooling
6. **Command Automation**: Full compatibility with Claude Code CLI commands

### Communication Flow

```
┌─────────────────────────────────────────┐
│  Browser (React App on :CLIENT_PORT)    │
│  - Components (Shadcn UI)               │
│  - State Management (React hooks)       │
│  - API Client (typed fetch wrapper)     │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST
                  │ /api/* proxied by Vite
                  ↓
┌─────────────────────────────────────────┐
│  FastAPI Server (:SERVER_PORT)          │
│  - REST API endpoints                   │
│  - Business logic services              │
│  - Database layer                       │
│  - Security & validation                │
└─────────────────────────────────────────┘
```

---

## Environment Configuration

### Overview

All ports and environment-specific configuration are managed through `.env` files. This allows for:
- ✅ **Flexible deployment**: Different ports per environment (dev/staging/prod)
- ✅ **Multi-instance support**: Run multiple apps on same machine
- ✅ **ADW compatibility**: Configure ports for automated workflows
- ✅ **No hardcoded values**: All configuration externalized

### Environment Files Structure

```
project-root/
├── .env                      # Root environment (for scripts & ADW)
├── .sample.env               # Root environment template
├── app/
│   ├── client/
│   │   ├── .env.local        # Client-specific environment (gitignored)
│   │   └── .env.sample       # Client environment template
│   └── server/
│       ├── .env              # Server environment (gitignored)
│       └── .env.sample       # Server environment template
```

### Root `.sample.env`

Create this file at project root for global configuration:

```bash
# =============================================================================
# Root Environment Configuration
# =============================================================================
# Copy this file to .env and configure for your environment
# Used by: scripts/start.sh, scripts/stop_apps.sh, ADW workflows

# -----------------------------------------------------------------------------
# Application Ports
# -----------------------------------------------------------------------------
CLIENT_PORT=5173              # Frontend dev server port
SERVER_PORT=8000              # Backend API server port

# -----------------------------------------------------------------------------
# ADW Configuration (AI Developer Workflow)
# -----------------------------------------------------------------------------
# GitHub Configuration
GITHUB_REPO_URL=https://github.com/owner/repository
GITHUB_PAT=                   # Optional: GitHub Personal Access Token

# Claude Configuration
ANTHROPIC_API_KEY=            # Required for ADW
CLAUDE_CODE_PATH=claude       # Path to Claude Code CLI

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
NODE_ENV=development
PYTHON_ENV=development
```

### Client `.env.sample` (`app/client/.env.sample`)

Create this file for frontend configuration:

```bash
# =============================================================================
# Frontend Environment Configuration
# =============================================================================
# Copy this file to .env.local and configure for your environment
# Note: Vite requires VITE_ prefix for environment variables

# -----------------------------------------------------------------------------
# Development Server
# -----------------------------------------------------------------------------
VITE_PORT=5173                # Frontend development server port

# -----------------------------------------------------------------------------
# API Configuration
# -----------------------------------------------------------------------------
VITE_API_URL=http://localhost:8000/api    # Backend API URL
VITE_API_TIMEOUT=30000        # API request timeout (ms)

# -----------------------------------------------------------------------------
# Feature Flags (Optional)
# -----------------------------------------------------------------------------
# VITE_ENABLE_ANALYTICS=false
# VITE_ENABLE_DEBUG=true
```

### Server `.env.sample` (`app/server/.env.sample`)

Create this file for backend configuration:

```bash
# =============================================================================
# Backend Environment Configuration
# =============================================================================
# Copy this file to .env and configure for your environment

# -----------------------------------------------------------------------------
# Server Configuration
# -----------------------------------------------------------------------------
SERVER_PORT=8000              # Backend API server port
SERVER_HOST=0.0.0.0           # Server host (0.0.0.0 for all interfaces)
SERVER_RELOAD=true            # Enable auto-reload in development

# -----------------------------------------------------------------------------
# CORS Configuration
# -----------------------------------------------------------------------------
# Comma-separated list of allowed origins
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# -----------------------------------------------------------------------------
# API Keys (Add your keys here)
# -----------------------------------------------------------------------------
OPENAI_API_KEY=               # OpenAI API key
ANTHROPIC_API_KEY=            # Anthropic API key

# -----------------------------------------------------------------------------
# Database Configuration (Example)
# -----------------------------------------------------------------------------
# DATABASE_URL=sqlite:///./app.db
# DATABASE_POOL_SIZE=5

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
# SECRET_KEY=your-secret-key-here
# ALGORITHM=HS256
# ACCESS_TOKEN_EXPIRE_MINUTES=30

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Environment Variable Loading Order

**Root (.env)**:
- Loaded by: Shell scripts (`start.sh`, `stop_apps.sh`)
- Accessed by: Bash environment
- Priority: Lowest (can be overridden)

**Client (.env.local)**:
- Loaded by: Vite automatically
- Accessed by: `import.meta.env.VITE_*`
- Priority: High (overrides .env)
- **Note**: Must prefix with `VITE_`

**Server (.env)**:
- Loaded by: python-dotenv / pydantic-settings
- Accessed by: `settings.PORT`, `os.getenv()`
- Priority: High (application-specific)

### Port Configuration Best Practices

1. **Development**: Use default ports (5173, 8000)
2. **Multiple instances**: Increment ports (5174, 8001)
3. **Production**: Use reverse proxy, keep internal ports
4. **ADW**: Configure once in root `.env`, reused by scripts
5. **Consistency**: Same port values across all env files

---

## Directory Structure

### Complete Structure

```
project-root/
├── .env                              # Root environment (gitignored)
├── .sample.env                       # Root environment template
├── .gitignore                        # Git ignore rules
│
├── .claude/                          # Claude Code automation
│   ├── commands/                     # Slash commands (24 files)
│   └── ...
│
├── app/                              # Main application code
│   ├── client/                       # Frontend (React + TypeScript)
│   │   ├── .env.local                # Client environment (gitignored)
│   │   ├── .env.sample               # Client environment template
│   │   │
│   │   ├── public/                   # Static assets
│   │   │   ├── favicon.ico
│   │   │   └── sample-data/          # Optional: seed data
│   │   │
│   │   ├── src/
│   │   │   ├── components/           # React components
│   │   │   │   ├── ui/               # Shadcn UI components
│   │   │   │   │   ├── button.tsx
│   │   │   │   │   ├── card.tsx
│   │   │   │   │   ├── input.tsx
│   │   │   │   │   └── ...
│   │   │   │   ├── features/         # Feature-specific components
│   │   │   │   │   ├── auth/
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   └── ...
│   │   │   │   └── layout/           # Layout components
│   │   │   │       ├── Header.tsx
│   │   │   │       ├── Footer.tsx
│   │   │   │       └── Layout.tsx
│   │   │   │
│   │   │   ├── lib/                  # Utilities & helpers
│   │   │   │   ├── api/              # API client
│   │   │   │   │   ├── client.ts     # Main API client
│   │   │   │   │   └── types.ts      # API type definitions
│   │   │   │   └── utils.ts          # Shadcn utils (cn, etc.)
│   │   │   │
│   │   │   ├── hooks/                # Custom React hooks
│   │   │   │   ├── useApi.ts
│   │   │   │   ├── useAuth.ts
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── types/                # Shared TypeScript types
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   ├── pages/                # Page components
│   │   │   │   ├── Home.tsx
│   │   │   │   ├── NotFound.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── App.tsx               # Root component
│   │   │   ├── main.tsx              # App entry point
│   │   │   └── index.css             # Global styles + Tailwind
│   │   │
│   │   ├── .gitignore
│   │   ├── components.json           # Shadcn config
│   │   ├── eslint.config.js          # ESLint config
│   │   ├── index.html                # HTML entry
│   │   ├── package.json              # Dependencies & scripts
│   │   ├── postcss.config.js         # PostCSS config
│   │   ├── tailwind.config.js        # Tailwind v4 config
│   │   ├── tsconfig.json             # TypeScript config
│   │   ├── tsconfig.node.json        # Node TypeScript config
│   │   └── vite.config.ts            # Vite config (port, proxy)
│   │
│   └── server/                       # Backend (FastAPI + Python)
│       ├── .env                      # Server environment (gitignored)
│       ├── .env.sample               # Server environment template
│       │
│       ├── core/                     # Core functionality
│       │   ├── __init__.py
│       │   ├── config.py             # Settings (env vars)
│       │   ├── security.py           # Auth, validation
│       │   └── dependencies.py       # FastAPI dependencies
│       │
│       ├── api/                      # API routes
│       │   ├── __init__.py
│       │   ├── routes/               # Route modules
│       │   │   ├── __init__.py
│       │   │   ├── health.py
│       │   │   └── ...               # Feature routes
│       │   └── main.py               # API router aggregation
│       │
│       ├── models/                   # Pydantic models
│       │   ├── __init__.py
│       │   └── schemas.py            # Request/Response schemas
│       │
│       ├── services/                 # Business logic
│       │   ├── __init__.py
│       │   └── ...                   # Service modules
│       │
│       ├── db/                       # Database layer
│       │   ├── __init__.py
│       │   └── database.py           # DB connection & models
│       │
│       ├── tests/                    # Backend tests
│       │   ├── __init__.py
│       │   ├── conftest.py           # Pytest fixtures
│       │   ├── test_api.py
│       │   └── ...
│       │
│       ├── .env.sample               # Environment template
│       ├── .gitignore
│       ├── main.py                   # FastAPI app instance
│       ├── pyproject.toml            # Python dependencies
│       ├── server.py                 # Server entry point
│       └── uv.lock                   # Dependency lock file
│
├── scripts/                          # Helper scripts
│   ├── start.sh                      # Start both servers
│   ├── stop_apps.sh                  # Stop all processes
│   ├── reset_db.sh                   # Reset database
│   └── copy_dot_env.sh               # Copy .env files
│
├── specs/                            # Feature specifications
├── adws/                             # AI Developer Workflow
├── agents/                           # Agent execution logs
├── logs/                             # Application logs
│
├── .gitignore                        # Git ignore rules
├── .env                              # Root environment vars
├── .sample.env                       # Sample environment
├── README.md                         # Project documentation
└── INFRASTRUCTURE_PLAN.md            # This file

```

### Key Directories Explained

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `app/client/src/components/ui/` | Shadcn UI components | Auto-generated by shadcn-ui |
| `app/client/src/lib/api/` | API client for FastAPI | `client.ts` (typed wrapper) |
| `app/server/core/` | Core backend utilities | `config.py`, `security.py` |
| `app/server/api/routes/` | API endpoint definitions | One file per feature area |
| `app/server/services/` | Business logic (testable) | Pure functions, no HTTP |
| `scripts/` | Automation scripts | Called by .claude/commands |

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3+ | UI framework |
| **TypeScript** | 5.8+ | Type safety |
| **Vite** | 6.0+ | Build tool & dev server |
| **Tailwind CSS** | 4.0+ | Utility-first CSS |
| **Shadcn UI** | Latest | Component library |
| **React Router** | 7.0+ | Client-side routing (optional) |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.115+ | API framework |
| **Python** | 3.10+ | Language |
| **uv** | Latest | Package manager |
| **Pydantic** | 2.0+ | Data validation |
| **pytest** | 8.0+ | Testing framework |
| **Uvicorn** | Latest | ASGI server |

### Development Tools

| Tool | Purpose |
|------|---------|
| **ESLint** | JavaScript linting |
| **Ruff** | Python linting |
| **Playwright** | E2E testing (MCP) |

---

## Command Compatibility Matrix

### Analysis of 24 Commands

| Command | Client Dependency | Server Dependency | Changes Needed |
|---------|-------------------|-------------------|----------------|
| `bug.md` | ✓ (test commands) | ✓ (test commands) | None (path compatible) |
| `chore.md` | ✓ (test commands) | ✓ (test commands) | None (path compatible) |
| `feature.md` | ✓ (references) | ✓ (references) | None (path compatible) |
| `patch.md` | ✓ (test commands) | ✓ (test commands) | None (path compatible) |
| `test.md` | ✓ (build/type check) | ✓ (pytest) | Update build commands |
| `test_e2e.md` | ✓ (URL) | ✓ (setup) | None (port compatible) |
| `start.md` | ✓ (port 5173) | ✓ (port 8000) | None (port compatible) |
| `install.md` | Implicit | ✓ (uv sync) | None |
| Other commands | N/A | N/A | None |

### Commands Requiring Updates (Only 1)

**`.claude/commands/test.md`** - Lines 44, 64, 70

#### Current (lines 44-70):
```bash
# Line 44: Python syntax check
Command: cd app/server && uv run python -m py_compile server.py main.py core/*.py

# Line 64: TypeScript check
Command: cd app/client && yarn type-check

# Line 70: Frontend build
Command: cd app/client && yarn build
```

#### Updated (for new stack):
```bash
# Line 44: Python syntax check
Command: cd app/server && uv run python -m py_compile server.py main.py core/*.py api/**/*.py services/*.py

# Line 64: TypeScript check
Command: cd app/client && yarn type-check

# Line 70: Frontend build
Command: cd app/client && yarn build
```

**All other 23 commands work without changes!**

---

## Migration Steps

### Phase 1: Backup Current State

```bash
# Create backup branch
git checkout -b backup-vanilla-stack
git add . && git commit -m "Backup: Vanilla TypeScript stack before migration"
git checkout master

# Or create a tarball
tar -czf backup-$(date +%Y%m%d).tar.gz app/
```

### Phase 2: Clear Client Directory

```bash
cd app/client

# Remove old files
rm -rf src/ public/ node_modules/ dist/
rm package.json package-lock.json tsconfig.json vite.config.ts

# Keep .gitignore if it exists
```

### Phase 2.5: Clean Server Directory (Remove Application-Specific Code)

```bash
cd app/server

# Remove application-specific core modules
# These are SQL-specific and not needed for generic template
rm -rf core/file_processor.py
rm -rf core/sql_processor.py
rm -rf core/sql_security.py
rm -rf core/insights.py
rm -rf core/llm_processor.py
rm -rf core/data_models.py
rm -rf core/constants.py

# Remove old main.py (we'll recreate it generically)
rm -f main.py

# Remove database files
rm -f db/*.db

# Keep these files:
# - server.py (will be updated)
# - pyproject.toml (will be updated)
# - tests/ directory structure
# - core/__init__.py (we'll recreate core/ with new files)

# Note: We'll recreate core/ with generic config.py, security.py, dependencies.py in later phases
```

### Phase 3: Initialize React + TypeScript + Vite

```bash
cd app/client

# Create React app with Vite
yarn create vite . --template react-ts

# Install dependencies
yarn install
```

### Phase 4: Install Tailwind CSS v4

```bash
cd app/client

# Install Tailwind v4
yarn add -D tailwindcss@next @tailwindcss/vite@next postcss autoprefixer

# Initialize Tailwind
yarn dlx tailwindcss init -p
```

### Phase 5: Install Shadcn UI

```bash
cd app/client

# Initialize Shadcn
yarn dlx shadcn@latest init

# Select options:
# - Style: Default
# - Base color: Slate (or your preference)
# - CSS variables: Yes

# Install initial components (recommended)
yarn dlx shadcn@latest add button
yarn dlx shadcn@latest add card
yarn dlx shadcn@latest add input
yarn dlx shadcn@latest add label
yarn dlx shadcn@latest add form
yarn dlx shadcn@latest add toast
```

### Phase 6: Configure Tailwind v4

Edit `app/client/src/index.css`:

```css
@import "tailwindcss";

/* IMPORTANT: Tailwind v4 requires reset in @layer base */
@layer base {
  * {
    box-sizing: border-box;
    padding: 0;
    margin: 0;
  }

  html, body {
    height: 100%;
  }
}

/* Your custom styles */
```

### Phase 7: Configure Vite (Port + Proxy)

Edit `app/client/vite.config.ts`:

```typescript
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')

  // Parse port from env or use default
  const port = parseInt(env.VITE_PORT || '5173')
  const apiUrl = env.VITE_API_URL || 'http://localhost:8000'

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port,
      strictPort: true,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
```

### Phase 8: Update package.json Scripts

Edit `app/client/package.json`:

```json
{
  "name": "client",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "type-check": "tsc --noEmit",
    "lint": "eslint . --ext ts,tsx"
  }
}
```

**Note**: Port is now read from `.env.local` (VITE_PORT), not hardcoded in scripts.

### Phase 9: Create API Client Structure

Create `app/client/src/lib/api/client.ts`:

```typescript
// API client configuration
// In dev: uses Vite proxy (/api -> http://localhost:SERVER_PORT/api)
// In prod: uses VITE_API_URL from environment
const API_BASE_URL = import.meta.env.DEV
  ? '/api'  // Proxy to backend in development
  : import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Generic API request function
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Export API methods
export const api = {
  // Health check
  async healthCheck() {
    return apiRequest<{ status: string }>('/health');
  },

  // Add your API methods here
  // Example:
  // async getData() {
  //   return apiRequest<DataResponse>('/data');
  // },
};
```

Create `app/client/src/lib/api/types.ts`:

```typescript
// API type definitions
export interface HealthCheckResponse {
  status: string;
  timestamp?: string;
}

// Add your API types here
```

### Phase 10: Create Utility Functions

Create `app/client/src/lib/utils.ts`:

```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### Phase 11: Setup Basic Layout

Create `app/client/src/components/layout/Layout.tsx`:

```typescript
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">App Name</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      <footer className="border-t mt-auto">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          © 2025 Your App
        </div>
      </footer>
    </div>
  );
}
```

### Phase 12: Update App.tsx

Edit `app/client/src/App.tsx`:

```typescript
import { Layout } from './components/layout/Layout';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';

function App() {
  return (
    <Layout>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Welcome</CardTitle>
            <CardDescription>
              React + TypeScript + Tailwind v4 + Shadcn + FastAPI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => alert('Hello!')}>
              Click me
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}

export default App;
```

### Phase 13: Server Restructure (Optional)

If you want to restructure the server (recommended for larger apps):

```bash
cd app/server

# Create new directories
mkdir -p api/routes models services

# Move existing files
mv main.py api/main.py  # If main.py has routes

# Create new files (shown in Phase 14)
```

### Phase 14: Create FastAPI Structure

Create `app/server/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routes import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["health"])

# Add your routers here
```

Create `app/server/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "App API"
    VERSION: str = "0.1.0"

    # Server Configuration (from environment)
    SERVER_PORT: int = 8000
    SERVER_HOST: str = "0.0.0.0"
    SERVER_RELOAD: bool = True

    # CORS - Parse comma-separated origins from env
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Add your settings here (API keys, database, etc.)

    class Config:
        env_file = ".env"
        case_sensitive = True

    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

settings = Settings()
```

Create `app/server/api/routes/health.py`:

```python
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

Create `app/server/models/schemas.py`:

```python
from pydantic import BaseModel
from typing import Optional

# Define your Pydantic models here
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: Optional[str] = None
```

### Phase 15: Update server.py

Edit `app/server/server.py`:

```python
#!/usr/bin/env python3
import uvicorn
from main import app
from core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
```

**Note**: All server configuration now comes from `.env` via `core/config.py`.

### Phase 16: Update pyproject.toml

Edit `app/server/pyproject.toml`:

```toml
[project]
name = "server"
version = "0.1.0"
description = "FastAPI Backend"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115.13",
    "uvicorn>=0.34.3",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.1",
    "python-multipart>=0.0.20",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.4.1",
    "httpx>=0.27.0",  # For testing FastAPI
]

[dependency-groups]
dev = [
    "ruff>=0.12.3",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

### Phase 17: Create Environment Files

Create root `.env`:

```bash
cd /path/to/project-root
cp .sample.env .env

# Edit .env with your configuration
# At minimum, set these:
# CLIENT_PORT=5173
# SERVER_PORT=8000
```

Create client `.env.local`:

```bash
cd app/client
cp .env.sample .env.local

# Edit .env.local with your configuration
# VITE_PORT=5173
# VITE_API_URL=http://localhost:8000/api
```

Create server `.env`:

```bash
cd app/server
cp .env.sample .env

# Edit .env with your API keys and configuration
# SERVER_PORT=8000
# ALLOWED_ORIGINS=http://localhost:5173
# Add your API keys here
```

**Important**: Ensure all three `.env` files have matching port values!

### Phase 17a: Update scripts/start.sh

Edit `scripts/start.sh` to use environment variables:

```bash
#!/bin/bash

# Load environment variables from root .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Port configuration from environment or defaults
SERVER_PORT=${SERVER_PORT:-8000}
CLIENT_PORT=${CLIENT_PORT:-5173}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Application...${NC}"
echo -e "${BLUE}Client Port: ${CLIENT_PORT}${NC}"
echo -e "${BLUE}Server Port: ${SERVER_PORT}${NC}"

# Function to kill process on port
kill_port() {
    local port=$1
    local process_name=$2

    # Find process using the port
    local pid=$(lsof -ti:$port 2>/dev/null)

    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Found $process_name running on port $port (PID: $pid). Killing it...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
        echo -e "${GREEN}$process_name on port $port has been terminated.${NC}"
    fi
}

# Kill any existing processes on our ports
kill_port $SERVER_PORT "backend server"
kill_port $CLIENT_PORT "frontend server"

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Check if .env exists in server directory
if [ ! -f "$PROJECT_ROOT/app/server/.env" ]; then
    echo -e "${RED}Warning: No .env file found in app/server/.${NC}"
    echo "Please:"
    echo "  1. cd app/server"
    echo "  2. cp .env.sample .env"
    echo "  3. Edit .env and add your API keys"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down services...${NC}"

    # Kill all child processes
    jobs -p | xargs -r kill 2>/dev/null

    # Wait for processes to terminate
    wait

    echo -e "${GREEN}Services stopped successfully.${NC}"
    exit 0
}

# Trap EXIT, INT, and TERM signals
trap cleanup EXIT INT TERM

# Start backend
echo -e "${GREEN}Starting backend server on port ${SERVER_PORT}...${NC}"
cd "$PROJECT_ROOT/app/server"
uv run python server.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend failed to start!${NC}"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting frontend server on port ${CLIENT_PORT}...${NC}"
cd "$PROJECT_ROOT/app/client"
yarn dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Frontend failed to start!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Services started successfully!${NC}"
echo -e "${BLUE}Frontend: http://localhost:${CLIENT_PORT}${NC}"
echo -e "${BLUE}Backend:  http://localhost:${SERVER_PORT}${NC}"
echo -e "${BLUE}API Docs: http://localhost:${SERVER_PORT}/docs${NC}"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user to press Ctrl+C
wait
```

**Key Changes**:
- Loads `.env` from project root
- Uses `$SERVER_PORT` and `$CLIENT_PORT` variables
- Shows configured ports in output
- Checks for .env before starting

### Phase 18: Update .claude/commands/test.md

Only change needed - update 3 lines as shown in [Command Compatibility Matrix](#commands-requiring-updates-only-1).

### Phase 19: Test the Setup

```bash
# First, ensure environment files are configured
# Root .env should have CLIENT_PORT=5173 and SERVER_PORT=8000
# app/client/.env.local should have VITE_PORT=5173
# app/server/.env should have SERVER_PORT=8000

# Terminal 1: Test using start script (recommended)
./scripts/start.sh  # Should start both servers using env vars

# Or manually in separate terminals:

# Terminal 1: Start backend
cd app/server
uv sync --all-extras
uv run python server.py  # Uses SERVER_PORT from .env

# Terminal 2: Start frontend
cd app/client
yarn install
yarn dev  # Uses VITE_PORT from .env.local

# Terminal 3: Test endpoints
# Note: URLs use ports from environment variables
open http://localhost:${CLIENT_PORT:-5173}
curl http://localhost:${SERVER_PORT:-8000}/api/health
```

### Phase 20: Verify Commands Work

```bash
# Test type checking
cd app/client && yarn type-check

# Test build
cd app/client && yarn build

# Test backend tests
cd app/server && uv run pytest

# Test backend linting
cd app/server && uv run ruff check .
```

### Phase 21: Commit

```bash
git add .
git commit -m "Setup: React + TypeScript + Tailwind v4 + Shadcn + FastAPI infrastructure

- Frontend: React 18 + TypeScript + Vite + Tailwind v4 + Shadcn UI
- Backend: FastAPI + Python + uv
- Full compatibility with .claude/commands/ automation
- Environment-based configuration (all ports configurable via .env)
- Ports: Configurable (default 5173 client, 8000 server)
- Ready for feature development"
```

### Phase 21.5: Add Test Infrastructure

**Frontend Testing (Vitest)**

```bash
cd app/client

# Install Vitest and testing utilities
yarn add -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# Update package.json to add test scripts
```

Edit `app/client/package.json` to add test script:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "type-check": "tsc --noEmit",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

Create `app/client/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

Create `app/client/src/test/setup.ts`:

```typescript
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})
```

Create example test `app/client/src/App.test.tsx`:

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders welcome message', () => {
    render(<App />)
    expect(screen.getByText(/Welcome/i)).toBeInTheDocument()
  })

  it('renders button', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /Click me/i })).toBeInTheDocument()
  })
})
```

**Backend Testing (Pytest)**

Backend already has pytest configured. Add example test:

Create `app/server/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
```

**Verify Tests Work**

```bash
# Test frontend
cd app/client
yarn test

# Test backend
cd app/server
uv run pytest -v

# Both should pass with example tests
```

---

## Future Project Setup

### Quick Start (Reusing This Template)

When starting a new project:

1. **Clone/Copy this structure**:
```bash
# Option 1: Clone this repo
git clone <this-repo> my-new-project
cd my-new-project
rm -rf .git
git init

# Option 2: Copy from template
cp -r /path/to/this/project /path/to/new-project
cd /path/to/new-project
```

2. **Update project metadata**:
```bash
# Update app/client/package.json name
# Update app/server/pyproject.toml name/description
# Update README.md
```

3. **Configure environment files**:
```bash
# Root environment
cp .sample.env .env
# Edit: CLIENT_PORT, SERVER_PORT, GITHUB_REPO_URL, ANTHROPIC_API_KEY

# Server environment
cd app/server
cp .env.sample .env
# Edit: SERVER_PORT, ALLOWED_ORIGINS, API keys

# Client environment
cd ../client
cp .env.sample .env.local
# Edit: VITE_PORT, VITE_API_URL

cd ../..
```

4. **Install dependencies**:
```bash
# Backend
cd app/server
uv sync --all-extras

# Frontend
cd ../client
yarn install

cd ../..
```

5. **Start development**:
```bash
./scripts/start.sh
# Will use ports from .env
```

6. **Start building features** from your PRD!

### Template Checklist

Before saving as a template, ensure:

- [ ] All dependencies installed and locked
- [ ] `.sample.env` files created at root with all required vars
- [ ] `app/client/.env.sample` created with VITE_* variables
- [ ] `app/server/.env.sample` created with SERVER_* variables
- [ ] **No actual `.env` or `.env.local` files committed** (add to .gitignore)
- [ ] No secrets in committed files
- [ ] Default ports documented (5173, 8000)
- [ ] README.md has project-specific info
- [ ] All commands tested and working
- [ ] scripts/start.sh uses environment variables
- [ ] Test infrastructure configured (Vitest + Pytest)
- [ ] Example tests created and passing
- [ ] Clean git history (or fresh init)

---

## Configuration Files

### Tailwind Config (`app/client/tailwind.config.js`)

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      // Shadcn theme customization
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### TypeScript Config (`app/client/tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path mapping */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### Vite Config (Full) - `app/client/vite.config.ts`

```typescript
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '')

  // Parse port from env or use default
  const port = parseInt(env.VITE_PORT || '5173')
  const apiUrl = env.VITE_API_URL || 'http://localhost:8000'

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port,
      strictPort: true,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
  }
})
```

**Environment Variables Used**:
- `VITE_PORT`: Development server port (default: 5173)
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

---

## Best Practices

### Frontend

1. **Component Organization**:
   - UI components in `components/ui/` (Shadcn)
   - Feature components in `components/features/`
   - Shared layouts in `components/layout/`

2. **Type Safety**:
   - Define API types in `lib/api/types.ts`
   - Share types with backend (consider monorepo tools)
   - Use strict TypeScript settings

3. **State Management**:
   - Start with React hooks (useState, useContext)
   - Add Zustand/Redux only when needed
   - Keep state close to usage

4. **Styling**:
   - Use Tailwind utility classes
   - Use Shadcn components for consistency
   - Custom CSS only for complex animations
   - Remember Tailwind v4 `@layer base` requirement

5. **API Calls**:
   - Centralize in `lib/api/client.ts`
   - Use custom hooks (e.g., `useApi`) for data fetching
   - Handle loading/error states consistently

### Backend

1. **Route Organization**:
   - One router per feature area
   - Keep routes thin (delegate to services)
   - Use dependency injection

2. **Business Logic**:
   - Pure functions in `services/`
   - Testable without HTTP layer
   - Clear input/output types (Pydantic)

3. **Error Handling**:
   - Use FastAPI's HTTPException
   - Return consistent error format
   - Log errors server-side

4. **Testing**:
   - Test services independently
   - Use FastAPI's TestClient for integration
   - Mock external dependencies

5. **Security**:
   - Validate all inputs (Pydantic)
   - Use environment variables for secrets
   - Implement rate limiting (production)
   - Sanitize database queries

### General

1. **Git Workflow**:
   - Commit early and often
   - Use semantic commit messages
   - Branch for features/fixes

2. **Documentation**:
   - Keep README.md updated
   - Document complex business logic
   - Add JSDoc/docstrings

3. **Environment**:
   - Never commit `.env` files
   - Keep `.env.sample` updated
   - Document all env vars

---

## Troubleshooting

### Common Issues

**1. Port Already in Use**

```bash
# Check your configured ports in .env files
cat .env | grep PORT
cat app/client/.env.local | grep VITE_PORT
cat app/server/.env | grep SERVER_PORT

# Kill process on configured client port (default 5173)
lsof -ti:${CLIENT_PORT:-5173} | xargs kill -9

# Kill process on configured server port (default 8000)
lsof -ti:${SERVER_PORT:-8000} | xargs kill -9

# Or use stop script (respects env vars)
./scripts/stop_apps.sh

# Alternatively, change ports in your .env files to avoid conflicts
```

**2. CORS Errors**

Check `app/server/.env`:
```bash
# Ensure your frontend URL is in ALLOWED_ORIGINS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Make sure it matches your VITE_PORT
```

Check `app/client/.env.local`:
```bash
# Ensure VITE_API_URL points to your backend
VITE_API_URL=http://localhost:8000/api

# Make sure it matches your SERVER_PORT
```

Verify Vite proxy in `vite.config.ts` uses env vars:
```typescript
const apiUrl = env.VITE_API_URL || 'http://localhost:8000'
proxy: {
  '/api': {
    target: apiUrl,
    changeOrigin: true,  // Important!
  }
}
```

**3. Tailwind Not Working**

Ensure `index.css` has:
```css
@import "tailwindcss";

@layer base {
  /* Your resets */
}
```

And `vite.config.ts` has:
```typescript
import tailwindcss from '@tailwindcss/vite'

plugins: [
  react(),
  tailwindcss(),  // Must be included
]
```

**4. Shadcn Components Not Found**

```bash
# Reinstall components
cd app/client
npx shadcn@latest add <component-name>

# Check components.json exists
cat components.json
```

**5. Type Errors in API Client**

Ensure `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "resolveJsonModule": true
  }
}
```

**6. Backend Tests Failing**

```bash
# Sync dependencies
cd app/server
uv sync --all-extras

# Run with verbose
uv run pytest -v

# Check Python version
python --version  # Should be 3.10+
```

---

## Appendix

### Port Reference

| Service | Default Port | Environment Variable | URL |
|---------|--------------|---------------------|-----|
| Frontend Dev | 5173 | `VITE_PORT` | http://localhost:{VITE_PORT} |
| Backend API | 8000 | `SERVER_PORT` | http://localhost:{SERVER_PORT} |
| API Docs | 8000 | `SERVER_PORT` | http://localhost:{SERVER_PORT}/docs |

**Note**: All ports are configurable via environment variables. See [Environment Configuration](#environment-configuration) section.

### Command Reference

| Command | Action |
|---------|--------|
| `yarn dev` | Start Vite dev server |
| `yarn build` | Build for production |
| `yarn type-check` | TypeScript type checking |
| `uv run python server.py` | Start FastAPI server |
| `uv run pytest` | Run backend tests |
| `uv run ruff check .` | Lint backend code |
| `./scripts/start.sh` | Start both servers |
| `./scripts/stop_apps.sh` | Stop all processes |

### Dependency Versions (Reference)

These are tested working versions:

**Frontend**:
- react: ^18.3.1
- typescript: ^5.8.3
- vite: ^6.3.5
- tailwindcss: ^4.0.0-alpha.x
- @tailwindcss/vite: ^4.0.0-alpha.x

**Backend**:
- fastapi: 0.115.13
- uvicorn: 0.34.3
- pydantic: ^2.0.0
- pytest: 8.4.1

---

## Next Steps

After completing this setup:

1. **Read your PRD** - Understand requirements
2. **Design data models** - Define Pydantic schemas
3. **Create API endpoints** - Build backend routes
4. **Build UI components** - Create React components
5. **Connect frontend to backend** - Use API client
6. **Write tests** - Backend + E2E
7. **Iterate** - Build features incrementally

---

## Conclusion

This infrastructure provides:

✅ Modern, type-safe frontend with React + TypeScript
✅ Fast development with Vite + HMR
✅ Beautiful UI with Tailwind v4 + Shadcn
✅ Robust backend with FastAPI + Python
✅ **Environment-based configuration** (all ports configurable)
✅ **Multi-instance support** (run multiple apps on same machine)
✅ **ADW-compatible** (automated workflows respect env config)
✅ Full automation support (.claude/commands/)
✅ **Complete test infrastructure** (Vitest + Pytest with examples)
✅ Production-ready architecture
✅ Reusable template for future projects

**Status**: Ready for implementation
**Next**: Execute migration steps or save as template

---

**Document Version**: 2.1.0
**Last Updated**: 2025-10-04
**Changes in v2.1**:
- Added Phase 2.5: Explicit server cleanup to remove SQL-specific code
- Standardized on Yarn v4 package manager throughout
- Added Phase 21.5: Complete test infrastructure with Vitest and example tests
- Previous v2.0: Environment-based port configuration for all services
**Maintained By**: Your Team
