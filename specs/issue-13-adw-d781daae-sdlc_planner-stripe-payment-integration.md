# Feature: Stripe Payment Integration for Course Dashboard & Paywall System

## Metadata
issue_number: `13`
adw_id: `d781daae`
issue_json: `{"number":13,"title":"stripe","body":"adw_plan_build_test_review\n\nimplmenet specs/PRD/pay-PRD.md\nmake sure ot use stripe mcp (configuredd on claude) to set everyting up.  if env are needed just give the user directions afterwards.  when doing testing make sure stripe goes to test mode not produciton mode"}`

## Feature Description
Implement a comprehensive Stripe payment integration system that enables a course dashboard with dynamic paywall functionality. The system displays free and paid courses, manages user entitlements through Stripe, handles checkout flows, and includes a referral credit system. All payment operations utilize the Stripe MCP server for setup and management, operating exclusively in test mode.

## User Story
As a logged-in user
I want to view available courses with clear pricing and access status
So that I can unlock paid content through Stripe checkout and track my course entitlements

## Problem Statement
The platform needs a unified course dashboard that differentiates between free and paid content while managing access control through Stripe payments. Users need a seamless way to discover courses, understand pricing tiers (curriculum vs a-la-carte), complete purchases via Stripe, and receive automatic access upon successful payment. Additionally, a referral system should incentivize user growth through automated credits.

## Solution Statement
Build a full-stack payment integration using Stripe MCP for product/price management, FastAPI backend for checkout session creation and webhook handling, and React frontend for displaying course cards with dynamic paywall overlays. Implement database models to track user entitlements, referrals, and purchase history. Use magic link authentication as the foundation for user identification in Stripe.

## Relevant Files
Use these files to implement the feature:

- `README.md` - Project structure and setup patterns
- `app/server/main.py` - Register new payment routes
- `app/server/db/models.py` - Add payment-related database models (Payment, Entitlement, Referral tables)
- `app/server/models/schemas.py` - Add Pydantic schemas for payment requests/responses
- `app/server/core/config.py` - Add Stripe configuration (API keys, webhook secrets)
- `app/server/api/routes/courses.py` - Extend with entitlement checking logic
- `app/server/db/database.py` - Database session management
- `app/client/src/lib/api/client.ts` - Add Stripe checkout API methods
- `app/client/src/pages/CourseLanding.tsx` - Update to dashboard view with course cards
- `app/client/src/context/AuthContext.tsx` - Current auth context for user email
- `app_docs/patterns/backend-routes.md` - Backend route patterns
- `app_docs/patterns/frontend-hooks.md` - Frontend hook patterns
- `.claude/commands/conditional_docs.md` - Testing documentation triggers
- `.claude/commands/test_e2e.md` - E2E test execution pattern

### New Files

- `app/server/api/routes/payments.py` - Stripe payment routes (checkout session, webhook handler, entitlement checks)
- `app/server/services/stripe_service.py` - Stripe MCP integration service (products, checkout, webhooks)
- `app/server/services/entitlement_service.py` - User entitlement management
- `app/server/services/referral_service.py` - Referral tracking and credit management
- `app/client/src/hooks/useStripeCheckout.ts` - Hook for initiating Stripe checkout
- `app/client/src/hooks/useCourseEntitlements.ts` - Hook for fetching user entitlements
- `app/client/src/components/courses/CourseCard.tsx` - Course card component with paywall overlay
- `app/client/src/components/courses/PaywallOverlay.tsx` - Locked course overlay component
- `app/client/src/pages/Dashboard.tsx` - Main course dashboard page
- `app/client/src/pages/CourseDetail.tsx` - Individual course detail page with module access
- `app/client/src/pages/CheckoutSuccess.tsx` - Post-checkout success page
- `app/client/src/pages/CheckoutCancel.tsx` - Checkout cancellation page
- `app/server/tests/test_payments.py` - Payment route tests
- `app/server/tests/test_stripe_service.py` - Stripe service tests
- `app/server/tests/test_entitlement_service.py` - Entitlement service tests
- `app/server/tests/test_referral_service.py` - Referral service tests
- `.claude/commands/e2e/test_stripe_checkout.md` - E2E test for Stripe checkout flow
- `.claude/commands/e2e/test_course_access.md` - E2E test for course access validation

## Implementation Plan

### Phase 1: Foundation
Set up Stripe MCP integration, database schema extensions, and configuration. Use Stripe MCP to create test products, prices, and configure webhook endpoints. Establish core services for Stripe operations and entitlement management.

### Phase 2: Core Implementation
Build backend routes for checkout session creation, webhook handling, and entitlement queries. Implement frontend course dashboard with dynamic card rendering based on entitlement status. Integrate paywall overlays and checkout flow.

### Phase 3: Integration
Connect all pieces: course cards trigger Stripe checkout, webhooks update entitlements, dashboard reflects purchase status. Add referral system, success/cancel pages, and comprehensive E2E tests.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Database Schema & Models
- Read `app/server/db/models.py` to understand current schema
- Extend `User` model to add referral fields:
  - `referral_code` (String, unique, indexed)
  - `referral_credits` (Integer, default 0)
  - `stripe_customer_id` (String, nullable, unique)
- Create new `Entitlement` model:
  - `id` (Integer, primary key)
  - `user_id` (ForeignKey to users)
  - `stripe_price_id` (String, indexed)
  - `stripe_payment_intent_id` (String, unique)
  - `status` (String: active, expired, refunded)
  - `created_at` (DateTime)
- Create new `Referral` model:
  - `id` (Integer, primary key)
  - `referrer_id` (ForeignKey to users)
  - `referee_email` (String)
  - `course_id` (String)
  - `stripe_payment_intent_id` (String)
  - `status` (String: pending, confirmed, credited)
  - `created_at` (DateTime)
- Create new `StripeProduct` model for local caching:
  - `id` (String, primary key - Stripe product ID)
  - `name` (String)
  - `description` (Text)
  - `category` (String: free, curriculum, alacarte)
  - `active` (Boolean)
  - `metadata` (JSON)
  - `updated_at` (DateTime)
- Create new `StripePrice` model for local caching:
  - `id` (String, primary key - Stripe price ID)
  - `product_id` (ForeignKey to StripeProduct)
  - `amount` (Integer - in cents)
  - `currency` (String)
  - `active` (Boolean)
  - `metadata` (JSON)
  - `updated_at` (DateTime)
- Run database migration/initialization to create new tables

### 2. Stripe MCP Setup & Configuration
- Read `app/server/core/config.py` to understand config patterns
- Add Stripe configuration settings:
  - `STRIPE_PUBLISHABLE_KEY` (from env, optional for server)
  - `STRIPE_SECRET_KEY` (from env, required)
  - `STRIPE_WEBHOOK_SECRET` (from env, required for webhook validation)
  - `STRIPE_TEST_MODE` (Boolean, default True)
- Use Stripe MCP to create test products in Stripe:
  - Free intro course (no price needed)
  - "AI in 4 Weekends" curriculum course with price
  - A-la-carte courses with individual prices
- Document all created Stripe product IDs and price IDs for reference
- Use Stripe MCP to set up webhook endpoint configuration (note: actual webhook URL will be added after route creation)

### 3. Pydantic Schemas
- Read `app/server/models/schemas.py` to understand schema patterns
- Create `CheckoutSessionRequest`:
  - `price_id` (str)
  - `referrer_code` (Optional[str])
- Create `CheckoutSessionResponse`:
  - `checkout_url` (str)
  - `session_id` (str)
- Create `WebhookEvent`:
  - `type` (str)
  - `data` (dict)
- Create `EntitlementResponse`:
  - `price_id` (str)
  - `product_id` (str)
  - `product_name` (str)
  - `status` (str)
  - `created_at` (datetime)
- Create `ReferralResponse`:
  - `referral_code` (str)
  - `total_referrals` (int)
  - `pending_referrals` (int)
  - `total_credits` (int)
- Create `StripeProductResponse`:
  - `id` (str)
  - `name` (str)
  - `description` (Optional[str])
  - `category` (str)
  - `price` (Optional[int])
  - `price_id` (Optional[str])
  - `currency` (str)
- Write unit tests for schema validation in `app/server/tests/test_schemas.py`

### 4. Stripe Service Layer
- Create `app/server/services/stripe_service.py`
- Implement functions using Stripe MCP:
  - `create_checkout_session(price_id: str, user_email: str, referrer_code: Optional[str] = None) -> dict` - Creates Stripe checkout session with metadata
  - `verify_webhook_signature(payload: bytes, signature: str) -> dict` - Validates webhook events
  - `get_or_create_customer(email: str) -> str` - Gets or creates Stripe customer ID
  - `sync_products() -> List[dict]` - Fetches all products from Stripe and caches locally
  - `sync_prices() -> List[dict]` - Fetches all prices from Stripe and caches locally
  - `get_customer_payment_intents(customer_id: str) -> List[dict]` - Gets payment history
  - `create_refund(payment_intent_id: str, amount: Optional[int] = None) -> dict` - Creates refund for referral credits
- Write comprehensive unit tests in `app/server/tests/test_stripe_service.py` with mocked Stripe MCP responses

### 5. Entitlement Service Layer
- Create `app/server/services/entitlement_service.py`
- Implement async functions:
  - `grant_entitlement(user_id: int, price_id: str, payment_intent_id: str, db: AsyncSession) -> Entitlement` - Creates entitlement record
  - `check_entitlement(user_id: int, price_id: str, db: AsyncSession) -> bool` - Checks if user has active entitlement
  - `get_user_entitlements(user_id: int, db: AsyncSession) -> List[Entitlement]` - Returns all user entitlements
  - `revoke_entitlement(entitlement_id: int, db: AsyncSession) -> None` - Marks entitlement as refunded
- Write unit tests in `app/server/tests/test_entitlement_service.py` with async database fixtures

### 6. Referral Service Layer
- Create `app/server/services/referral_service.py`
- Implement async functions:
  - `generate_referral_code(user_id: int) -> str` - Generates unique 8-char referral code
  - `validate_referral_code(code: str, db: AsyncSession) -> Optional[User]` - Validates and returns referrer
  - `create_referral(referrer_id: int, referee_email: str, payment_intent_id: str, db: AsyncSession) -> Referral` - Creates pending referral
  - `confirm_referral(referral_id: int, db: AsyncSession) -> None` - Marks referral as confirmed
  - `apply_referral_credit(referrer_id: int, amount: int, db: AsyncSession) -> None` - Updates user credit balance
  - `get_referral_stats(user_id: int, db: AsyncSession) -> dict` - Returns referral statistics
- Write unit tests in `app/server/tests/test_referral_service.py`

### 7. Payment Routes
- Read `app_docs/patterns/backend-routes.md` for route patterns
- Create `app/server/api/routes/payments.py`
- Implement routes:
  - `POST /api/payments/checkout` - Creates Stripe checkout session (requires auth)
    - Accepts `CheckoutSessionRequest`
    - Validates referrer code if provided
    - Calls `stripe_service.create_checkout_session()`
    - Returns `CheckoutSessionResponse`
  - `POST /api/payments/webhook` - Handles Stripe webhooks (no auth required)
    - Validates webhook signature
    - Handles `payment_intent.succeeded` event
    - Grants entitlements via `entitlement_service`
    - Processes referrals via `referral_service`
    - Returns 200 OK
  - `GET /api/payments/entitlements` - Gets user entitlements (requires auth)
    - Returns list of `EntitlementResponse`
  - `GET /api/payments/referrals` - Gets user referral stats (requires auth)
    - Returns `ReferralResponse`
  - `POST /api/payments/sync-products` - Admin route to sync products from Stripe
    - Calls `stripe_service.sync_products()` and `sync_prices()`
    - Updates local database cache
    - Returns count of synced products
- Register payment router in `app/server/main.py` with prefix `/api/payments`
- Write comprehensive route tests in `app/server/tests/test_payments.py` using TestClient and mocked services

### 8. Update Courses Routes
- Read `app/server/api/routes/courses.py`
- Extend `GET /api/courses` to include pricing information:
  - Join with `StripeProduct` and `StripePrice` tables
  - Return enriched course data with price_id, amount, category
- Add `GET /api/courses/{course_id}/check-access` endpoint:
  - Requires authentication
  - Checks user entitlements via `entitlement_service`
  - Returns boolean access status
- Update tests in `app/server/tests/test_courses.py`

### 9. Frontend API Client Extensions
- Read `app/client/src/lib/api/client.ts`
- Add Stripe-related API methods:
  - `createCheckoutSession(priceId: string, referrerCode?: string): Promise<{checkout_url: string, session_id: string}>`
  - `getUserEntitlements(): Promise<EntitlementResponse[]>`
  - `getReferralStats(): Promise<ReferralResponse>`
  - `syncStripeProducts(): Promise<{count: number}>`
  - `checkCourseAccess(courseId: number): Promise<{has_access: boolean}>`
- Add TypeScript types in `app/client/src/lib/api/types.ts`:
  - `CheckoutSessionResponse`
  - `EntitlementResponse`
  - `ReferralResponse`
  - `StripeProductResponse`

### 10. Frontend Hooks
- Read `app_docs/patterns/frontend-hooks.md` for hook patterns
- Create `app/client/src/hooks/useStripeCheckout.ts`:
  - Manages checkout loading/error states
  - Provides `initiateCheckout(priceId: string, referrerCode?: string)` function
  - Redirects to Stripe checkout URL on success
- Create `app/client/src/hooks/useCourseEntitlements.ts`:
  - Fetches user entitlements on mount
  - Returns `{entitlements, loading, error, refetch}`
  - Provides helper function `hasAccess(priceId: string): boolean`
- Create `app/client/src/hooks/useReferralStats.ts`:
  - Fetches referral statistics
  - Returns `{stats, loading, error}`
- Write frontend tests for hooks using React Testing Library

### 11. Course Card Components
- Create `app/client/src/components/courses/CourseCard.tsx`:
  - Props: `course` (StripeProductResponse), `hasAccess` (boolean)
  - Displays course title, description, price
  - Conditional rendering based on category (free/curriculum/alacarte)
  - Shows "Access Now" for free courses or purchased courses
  - Shows paywall overlay for locked courses
  - Integrates with `useStripeCheckout` hook
- Create `app/client/src/components/courses/PaywallOverlay.tsx`:
  - Semi-transparent overlay with blur effect
  - "Unlock Access" button
  - Displays price and category
  - Triggers checkout on button click
- Create component tests using Vitest

### 12. Dashboard Page
- Read existing `app/client/src/pages/CourseLanding.tsx` for reference
- Create `app/client/src/pages/Dashboard.tsx`:
  - Protected route (requires authentication)
  - Fetches courses via `GET /api/courses`
  - Uses `useCourseEntitlements` hook
  - Groups courses by category (Free, Curriculum, A-La-Carte)
  - Renders `CourseCard` components with entitlement checks
  - Shows "Welcome Back" header with user email
  - Displays referral card with stats and referral link
- Update `app/client/src/App.tsx` to add `/dashboard` route

### 13. Course Detail Page
- Create `app/client/src/pages/CourseDetail.tsx`:
  - Route: `/course/:courseId`
  - Protected route with entitlement check
  - Fetches course details and checks access via `checkCourseAccess`
  - Redirects to dashboard if no access
  - Displays course overview, module list
  - Placeholder for future module content
  - "Upgrade" CTA if partial access

### 14. Checkout Success/Cancel Pages
- Create `app/client/src/pages/CheckoutSuccess.tsx`:
  - Route: `/checkout/success`
  - Confirms successful payment
  - Shows "Processing your access..." message
  - Provides link back to dashboard
  - Optionally polls entitlements until access is granted
- Create `app/client/src/pages/CheckoutCancel.tsx`:
  - Route: `/checkout/cancel`
  - Informs user checkout was cancelled
  - Provides "Return to Dashboard" button

### 15. E2E Test: Stripe Checkout Flow
- Read `.claude/commands/test_e2e.md` to understand E2E test patterns
- Read `.claude/commands/e2e/test_registration_flow.md` as an example
- Create `.claude/commands/e2e/test_stripe_checkout.md`:
  - User Story: Test complete checkout flow from dashboard to success
  - Test Steps:
    1. Navigate to dashboard (logged in)
    2. Verify locked course card displays with price
    3. Click "Unlock Access" button
    4. Verify redirect to Stripe checkout URL (validate URL contains checkout.stripe.com)
    5. Note: Cannot complete actual Stripe checkout in test mode without Stripe test card form interaction
    6. Manually trigger webhook via Stripe CLI or mock webhook endpoint
    7. Return to dashboard
    8. Verify course card now shows "Access Now" button
    9. Click course to navigate to course detail page
    10. Verify access granted
  - Success Criteria: Checkout session created, webhook processed, entitlement granted
  - Screenshots: dashboard_locked.png, checkout_redirect.png, dashboard_unlocked.png, course_detail.png

### 16. E2E Test: Course Access Validation
- Create `.claude/commands/e2e/test_course_access.md`:
  - User Story: Validate access control for free vs paid courses
  - Test Steps:
    1. Navigate to dashboard (logged in)
    2. Identify free course card
    3. Click free course, verify immediate access to course detail
    4. Return to dashboard
    5. Identify locked paid course
    6. Attempt to navigate directly to `/course/{paid_course_id}`
    7. Verify redirect back to dashboard or access denied message
    8. Grant entitlement via admin API or database
    9. Navigate to paid course again
    10. Verify access granted
  - Success Criteria: Free courses accessible, paid courses blocked without entitlement, access granted after purchase
  - Screenshots: free_course_access.png, paid_course_blocked.png, paid_course_granted.png

### 17. Referral System Integration
- Update `app/client/src/pages/Dashboard.tsx` to display referral card:
  - Show referral link: `https://ai-in-4.crossgen-ai.com/ref/{referral_code}`
  - Display total referrals, pending referrals, total credits
  - Copy-to-clipboard functionality
- Create referral landing route in `app/client/src/App.tsx`:
  - Route: `/ref/:code`
  - Stores referral code in localStorage or session
  - Redirects to login/register with code preserved
- Update `app/server/api/routes/payments.py` checkout endpoint:
  - Accept referrer code from localStorage/session
  - Include in Stripe checkout metadata
- Update webhook handler to process referrals:
  - Extract referrer code from payment metadata
  - Create referral record
  - Apply 25% credit to referrer after payment success

### 18. Database Seeding
- Update or create `app/server/db/seed_db.py`:
  - Seed test users with referral codes
  - Seed sample entitlements
  - Seed sample referrals
- Run seed script to populate test data

### 19. Integration Testing
- Write integration tests that cover full workflows:
  - `app/server/tests/test_payment_integration.py`:
    - Test checkout session creation → webhook → entitlement grant
    - Test referral code validation → checkout → credit application
    - Test product sync from Stripe
- Ensure all tests use async database fixtures from `conftest.py`
- Read `app_docs/testing/README.md` if encountering test failures

### 20. Environment Configuration Documentation
- Document required environment variables for user:
  - `STRIPE_SECRET_KEY` - Get from Stripe Dashboard (test mode)
  - `STRIPE_PUBLISHABLE_KEY` - Get from Stripe Dashboard (test mode)
  - `STRIPE_WEBHOOK_SECRET` - Get from Stripe CLI or Dashboard webhook settings
  - `STRIPE_TEST_MODE=true` - Ensures test mode
- Provide instructions for Stripe webhook local testing:
  - Install Stripe CLI
  - Run `stripe listen --forward-to http://localhost:8000/api/payments/webhook`
  - Copy webhook signing secret to `.env`
- Update `app/server/.env.sample` with Stripe variables

### 21. Validation Commands Execution
- Run all validation commands to ensure zero regressions
- Execute E2E tests as documented in step 15 and 16
- Verify all unit and integration tests pass
- Confirm TypeScript compilation succeeds
- Validate frontend build completes without errors

## Testing Strategy

### Unit Tests
- Pydantic schema validation tests (field validators, data types)
- Stripe service tests with mocked MCP responses (checkout, webhooks, customers)
- Entitlement service tests with async database fixtures (grant, check, revoke)
- Referral service tests (code generation, validation, credit application)
- Payment route tests with mocked services (checkout, webhook, entitlements)
- Frontend hook tests with mocked API client (checkout, entitlements, referrals)
- React component tests (CourseCard, PaywallOverlay rendering states)

### Integration Tests
- Full payment workflow: checkout → webhook → entitlement grant
- Referral workflow: code validation → checkout metadata → credit application
- Product sync from Stripe to local database
- Course access checks with entitlement validation

### E2E Tests
- Complete Stripe checkout flow from dashboard to course access
- Access control validation for free vs paid courses
- Referral link flow and credit tracking

### Edge Cases
- Invalid referral codes during checkout
- Duplicate webhook events (idempotency)
- Expired or revoked entitlements
- Refund processing and entitlement revocation
- User without Stripe customer record
- Missing or invalid Stripe product/price IDs
- Checkout session expiration
- Multiple simultaneous checkouts for same user
- Self-referral prevention
- Referral credit cap enforcement

## Acceptance Criteria
- [ ] User can view dashboard with free and paid courses clearly differentiated
- [ ] Locked courses display paywall overlay with price and unlock button
- [ ] Clicking unlock initiates Stripe checkout session and redirects to Stripe
- [ ] Successful payment triggers webhook that grants entitlement automatically
- [ ] User's dashboard updates to show newly purchased courses as accessible
- [ ] User can access course detail page only for entitled courses
- [ ] Referral code generation and validation works correctly
- [ ] Referral credits apply automatically after referred user's successful payment
- [ ] All Stripe operations use test mode (no production charges)
- [ ] All tests pass (unit, integration, E2E)
- [ ] TypeScript compilation succeeds with no errors
- [ ] Frontend build completes successfully
- [ ] Environment variables are documented for user setup
- [ ] Webhook signature validation prevents unauthorized access
- [ ] Database migrations create all required tables and relationships

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_stripe_checkout.md` to validate Stripe checkout functionality
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_course_access.md` to validate course access control
- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/server && uv run pytest tests/test_payments.py -v` - Run payment route tests specifically
- `cd app/server && uv run pytest tests/test_stripe_service.py -v` - Run Stripe service tests
- `cd app/server && uv run pytest tests/test_entitlement_service.py -v` - Run entitlement service tests
- `cd app/server && uv run pytest tests/test_referral_service.py -v` - Run referral service tests
- `cd app/client && bun tsc --noEmit` - Run frontend type checking to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions
- `cd app/client && bun test` - Run frontend unit tests

## Notes

### Stripe MCP Usage
- All Stripe operations should use the configured Stripe MCP server
- Reference available MCP functions like `mcp__stripe__create_checkout_session`, `mcp__stripe__list_products`, `mcp__stripe__create_price`, etc.
- Use test mode exclusively: all API keys should be test keys (prefixed with `sk_test_` and `pk_test_`)
- Stripe CLI useful for local webhook testing: `stripe listen --forward-to localhost:8000/api/payments/webhook`

### Test Mode Enforcement
- Set `STRIPE_TEST_MODE=true` in environment configuration
- Validate all API keys are test keys in `stripe_service.py` initialization
- Add runtime checks to prevent production mode usage

### Future Considerations
- Implement subscription-based pricing for cohort courses (recurring payments)
- Add progress tracking percentage for courses
- Implement course completion certificates
- Add email notifications via Postmark for purchase confirmations and referral credits
- Admin dashboard for viewing user purchases and referral analytics
- Cohort scheduling with start dates
- Coupon code support beyond referral credits
- Multi-currency support
- Failed payment retry logic
- Partial refunds for referral adjustments

### Security Considerations
- Webhook signature validation is critical - never skip this check
- User authentication required for all entitlement and checkout routes
- Prevent self-referrals by validating referrer email ≠ referee email
- Implement rate limiting on checkout endpoint to prevent abuse
- Never expose Stripe secret keys in frontend code
- Sanitize all user inputs in referral codes and metadata

### Database Migration Strategy
- Use SQLAlchemy's `metadata.create_all()` for development
- For production, consider Alembic for proper migration management
- Ensure backward compatibility with existing User and Course records
- Add indexes on frequently queried fields (stripe_customer_id, stripe_price_id, referral_code)

### Dependencies to Add
- None required - Stripe MCP server is already configured
- Ensure `sqlalchemy[asyncio]` is available for async database operations
- Ensure `pydantic[email]` is available for email validation
