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

## Testing Documentation Triggers

- app_docs/testing/README.md
  - Conditions:
    - When creating or modifying tests
    - When fixing test failures
    - When working with pytest or test files
    - When debugging test errors
    - When implementing test-related features

- app_docs/testing/stack_guides/async_database_tests.md
  - Conditions:
    - When working with async database tests
    - When testing SQLAlchemy async code
    - When encountering greenlet errors
    - When testing database fixtures or sessions
    - When dealing with relationship loading in tests

- app_docs/testing/stack_guides/fastapi_route_tests.md
  - Conditions:
    - When testing FastAPI routes or endpoints
    - When working with mocks in API tests
    - When encountering "mock not called" errors
    - When testing Pydantic model validation
    - When using AsyncMock in tests

- app_docs/testing/failure_patterns/greenlet_errors.md
  - Conditions:
    - When seeing "MissingGreenlet" errors
    - When tests fail with greenlet spawn errors
    - When lazy-loading relationships fail in tests

- app_docs/testing/failure_patterns/mock_import_paths.md
  - Conditions:
    - When mocks are not being called in tests
    - When encountering mock import path issues
    - When patch decorators seem ineffective

- app_docs/testing/failure_patterns/pydantic_mock_validation.md
  - Conditions:
    - When Pydantic validation fails with mock objects
    - When seeing "Input should be a valid string" errors with AsyncMock
    - When response model validation fails in tests

- app_docs/testing/stack_guides/stripe_webhook_tests.md
  - Conditions:
    - When testing Stripe webhook handlers or payment integrations
    - When running payment_intent webhook tests
    - When seeing "webhook signature verification failed" errors
    - When testing entitlement granting after payment
    - When testing referral credit application
    - When working with test_payment_integration.py

- app_docs/testing/STRIPE_TESTING.md
  - Conditions:
    - When testing Stripe payment integration end-to-end
    - When setting up Stripe test mode vs live mode
    - When testing employment-based pricing logic
    - When testing course access control (free, alacarte, curriculum)
    - When using Stripe CLI for local webhook testing
    - When debugging checkout session creation
    - When verifying payment_intent metadata flow
    - When testing with Stripe test cards
    - When troubleshooting "course remains locked after payment"
    - When verifying price selection based on employment status
    - When testing alacarte per-course vs curriculum bundle access
    - When running create_test_products.py script
    - When switching between test and live mode
    - When performing manual or E2E Stripe testing
    - When implementing or testing referral system with Stripe payments  # NEW
    - When handling refunded payments or revoked entitlements  # NEW
    - When configuring product metadata in Stripe dashboard  # NEW
    - When diagnosing "No price available" errors  # NEW
    - When working with stripe_service.py or webhook signature verification  # NEW
    - When deploying Stripe integration to production  # NEW