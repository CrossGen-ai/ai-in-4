# Code Patterns

This directory contains templates and patterns for implementing features in this application.

## Overview

These pattern documents serve as reference guides for implementing common features and functionality. They provide standardized approaches that maintain consistency across the codebase.

## Available Patterns

- [Backend Routes](backend-routes.md) - How to create new API endpoints with FastAPI
- [Frontend Hooks](frontend-hooks.md) - How to create custom React hooks

## When to Use These

These patterns are automatically referenced by ADW commands (`/feature`, `/bug`, `/chore`) when relevant conditions are met. They're also discoverable through `.claude/commands/conditional_docs.md` for manual reference.

### Automatic Discovery

When you run commands like `/feature "Add user authentication"`, the ADW system:
1. Reads `conditional_docs.md`
2. Identifies relevant patterns based on the task
3. Includes pattern documentation in the implementation plan
4. Ensures consistent code structure

## Working Examples

Each pattern references working examples in the codebase that you can examine:

- **Backend Route:** `app/server/api/routes/health.py` - Minimal working API endpoint
- **Frontend Hook:** `app/client/src/hooks/useHealth.ts` - Complete custom hook with API integration
- **Backend Test:** `app/server/tests/test_health.py` - API endpoint testing pattern

## Pattern Philosophy

1. **Consistency:** Follow established patterns for predictable code structure
2. **Type Safety:** Use TypeScript + Pydantic for end-to-end validation
3. **Simplicity:** Keep patterns straightforward and maintainable
4. **Examples:** Every pattern includes working code examples

## Adding New Patterns

When adding a new pattern to this directory:

1. Create the pattern document in `app_docs/patterns/`
2. Include code examples and working references
3. Update this README with a link to the new pattern
4. Add discovery conditions to `.claude/commands/conditional_docs.md`
5. Reference working examples from the codebase when possible

## See Also

- [Infrastructure Plan](../../INFRASTRUCTURE_PLAN.md) - Detailed architecture documentation
- [README](../../README.md) - Project overview and setup
- [Test Patterns](../../app/server/tests/README.md) - Backend testing patterns
