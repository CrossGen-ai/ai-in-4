# Conditional Documentation Guide

This prompt helps you determine what documentation you should read based on the specific changes you need to make in the codebase. Review the conditions below and read the relevant documentation before proceeding with your task.

## Instructions
- Review the task you've been asked to perform
- Check each documentation path in the Conditional Documentation section
- For each path, evaluate if any of the listed conditions apply to your task
  - IMPORTANT: Only read the documentation if any one of the conditions match your task
- IMPORTANT: You don't want to excessively read documentation. Only read the documentation if it's relevant to your task.

## Conditional Documentation

- README.md
  - Conditions:
    - When operating on anything under app/server
    - When operating on anything under app/client
    - When first understanding the project structure
    - When you want to learn the commands to start or stop the server or client

- app/client/src/style.css
  - Conditions:
    - When you need to make changes to the client's style

- .claude/commands/classify_adw.md
  - Conditions:
    - When adding or removing new `adws/adw_*.py` files

- adws/README.md
  - Conditions:
    - When you're operating in the `adws/` directory

- app_docs/patterns/README.md
  - Conditions:
    - When creating new features
    - When you want to understand code patterns and conventions
    - When implementing new functionality
    - When you need to see available pattern templates

- app_docs/patterns/backend-routes.md
  - Conditions:
    - When creating new API endpoints
    - When adding routes to the backend
    - When implementing backend features that require HTTP endpoints
    - When you need to understand FastAPI route patterns
    - When adding new functionality to app/server/api/routes/

- app_docs/patterns/frontend-hooks.md
  - Conditions:
    - When creating custom React hooks
    - When implementing data fetching in the frontend
    - When adding hooks to app/client/src/hooks/
    - When you need to understand React hook patterns
    - When integrating with the API client

- app/client/src/hooks/useHealth.ts
  - Conditions:
    - When creating custom hooks (working example to reference)
    - When implementing API integration in hooks (see actual implementation)
    - When you need a complete hook example with error handling and loading states

- app_docs/feature-3e81e604-ai-course-platform-mvp.md
  - Conditions:
    - When working with authentication or magic link functionality
    - When implementing user registration or experience assessment features
    - When modifying the course platform landing, login, or registration pages
    - When troubleshooting magic link token generation or validation
    - When adding new authentication routes or user management endpoints
    - When working with the AuthContext or protected routes
    - When updating database models for users, experiences, or magic links