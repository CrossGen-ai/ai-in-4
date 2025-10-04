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

### Running ADW via GitHub Webhooks

If triggering ADW through GitHub webhooks (vs. terminal), the webhook server must be running:

```bash
PORT=8001 uv run adws/adw_triggers/trigger_webhook.py
```

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
