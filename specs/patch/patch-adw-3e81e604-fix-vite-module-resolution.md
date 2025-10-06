# Patch: Fix Vite Module Resolution Error for types.ts Exports

## Metadata
adw_id: `3e81e604`
review_change_request: `Critical module resolution error: Vite runtime cannot resolve exports from app/client/src/lib/api/types.ts. The browser console shows 'The requested module /src/lib/api/types.ts does not provide an export named AuthResponse' (and similar for User, UserCreate, etc.) even though all these interfaces are exported in the file. TypeScript compilation succeeds (yarn type-check passes), but the application fails to load in the browser with a blank page.

Suggested resolution: This appears to be a Vite module resolution or caching issue. Attempted fixes: cleared Vite cache, restarted dev server, removed extended file attributes. The types.ts file contains valid exports that TypeScript recognizes. Need to investigate potential circular dependencies, module loading order, or Vite configuration issues. May need to restructure imports or add explicit export statements.`

## Issue Summary
**Original Spec:** specs/issue-7-adw-3e81e604-sdlc_planner-ai-course-platform-mvp.md
**Issue:** Vite runtime fails to resolve exports from `app/client/src/lib/api/types.ts` at runtime despite TypeScript compilation succeeding. Browser console shows errors like "The requested module /src/lib/api/types.ts does not provide an export named AuthResponse" causing a blank page.
**Solution:** The issue is caused by the TypeScript compiler option `verbatimModuleSyntax: true` in `tsconfig.app.json` combined with interface-only exports. When this option is enabled, Vite requires explicit `export type` syntax for type-only exports. Converting all interface exports to use `export type` will resolve the module resolution error.

## Files to Modify
- `app/client/src/lib/api/types.ts` - Convert all interface exports to use `export type` syntax

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update types.ts to use explicit export type syntax
- Replace all `export interface` declarations with `export type` declarations
- This ensures Vite correctly handles type-only exports when `verbatimModuleSyntax: true` is enabled
- Keep all existing type definitions and structure intact

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd app/client && yarn type-check` - Verify TypeScript compilation still passes
2. `cd app/client && yarn build` - Verify production build succeeds
3. `./scripts/start.sh` - Start the application
4. Manual browser test: Navigate to `http://localhost:5173` and verify the application loads without console errors
5. Manual browser test: Check browser console for any module resolution errors related to types.ts
6. `cd app/server && uv run pytest tests/ -v --tb=short` - Verify backend tests pass

## Patch Scope
**Lines of code to change:** ~10 lines (8 interface declarations)
**Risk level:** low
**Testing required:** TypeScript type-check, frontend build, manual browser verification to confirm module resolution works at runtime
