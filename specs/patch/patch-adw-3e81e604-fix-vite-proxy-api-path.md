# Patch: Fix Vite Proxy API Path Double-Prefix Issue

## Metadata
adw_id: `3e81e604`
review_change_request: `Vite proxy configuration is not working - frontend API calls to /api/* endpoints return 404 errors even though backend is running and responding correctly at http://localhost:8000/api/*. Direct backend API calls work (tested with curl), but calls through the Vite dev server proxy fail.`

## Issue Summary
**Original Spec:** specs/issue-7-adw-3e81e604-sdlc_planner-ai-course-platform-mvp.md
**Issue:** The Vite proxy is configured to forward `/api` requests to `http://localhost:8000`, but the backend API routes already include the `/api` prefix. This causes a double-prefix issue where frontend requests to `/api/auth/register` get proxied to `http://localhost:8000/api/auth/register` (correct), but the API client is constructing URLs that result in `/api/api/auth/register`.
**Solution:** Fix the Vite proxy configuration to use `rewrite` to strip the `/api` prefix before forwarding to the backend, or update the API client to not include `/api` in development mode since the proxy already handles it. The cleanest solution is to configure the proxy to rewrite `/api` to `/api` on the backend without duplication.

## Files to Modify
- `app/client/vite.config.ts` - Update proxy configuration to properly rewrite API paths
- `app/client/src/lib/api/client.ts` - Ensure API_BASE_URL is correctly configured for dev/prod

## Implementation Steps

### Step 1: Fix Vite proxy configuration
- Update `app/client/vite.config.ts` proxy settings to use `rewrite` option
- Configure proxy to forward `/api/*` to `http://localhost:8000/api/*` without path duplication
- Ensure `changeOrigin: true` and `secure: false` are set for local development

### Step 2: Verify API client base URL configuration
- Confirm `app/client/src/lib/api/client.ts` uses `/api` in development mode
- Ensure the API client constructs URLs correctly (e.g., `/api` + `/auth/register` = `/api/auth/register`)
- Verify production mode uses full URL from VITE_API_URL environment variable

### Step 3: Test the proxy configuration
- Start both backend and frontend servers
- Test registration endpoint via browser DevTools Network tab
- Verify requests to `/api/auth/register` are proxied to `http://localhost:8000/api/auth/register`
- Confirm no 404 errors occur

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd app/server && uv run python -m py_compile server.py main.py core/*.py api/**/*.py services/*.py` - Verify backend syntax
2. `cd app/server && uv run ruff check .` - Verify backend code quality
3. `cd app/server && uv run pytest tests/ -v --tb=short` - Verify backend tests pass
4. `cd app/client && yarn type-check` - Verify TypeScript compilation
5. `cd app/client && yarn build` - Verify frontend builds successfully
6. Manual test: Start servers with `./scripts/start.sh` and verify registration flow works without 404 errors

## Patch Scope
**Lines of code to change:** ~5 (vite.config.ts only)
**Risk level:** low
**Testing required:** Manual verification of registration flow + existing test suite
