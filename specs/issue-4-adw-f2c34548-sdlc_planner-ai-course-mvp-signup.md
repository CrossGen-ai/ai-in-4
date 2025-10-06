# Feature: AI Course MVP - Signup and Authentication Platform

## Metadata
issue_number: `4`
adw_id: `f2c34548`
issue_json: `{"number":4,"title":"Initial Framewoork","body":"adw_plan_build_test_review\n\nWe are creating a web site course for teaching people to learn AI. I will be hosting learning sessions. This website is for signing up and paying for it as well as where to go to to get course materials after I'm done as well as the future upcoming schedule.  It will be at:  ai-in-4.crossgen-ai.com sub domain.\n\nInitial MVP:\n1) Landing page (react, tailwindscss, shadcn) follow the styling of www.crossgen-ai.com (logo and themes).  Keep the idea of \"humanizing the machine\" from the website\n2) a registration page - sign up\n3) regiraiton page should ingerview about their AI experiance and save the results.  to a user experience table\n3) Fast API backend.  Use magiclink for signup \n4) SQLlite database\n5) for fast log in with localhost by selecting a user to logon as and auto log in as that user.\n6) there should be a thank you registration page explaining magic link\n7) the login should go to a basic \"course\" landing page we will build out\n8) keep all design responsive for mobile, tablet, and desktop"}`

## Feature Description
Build a comprehensive AI learning course platform MVP that enables users to sign up, authenticate via magic link, provide their AI experience information, and access course materials. The platform will feature a modern landing page following the CrossGen AI brand aesthetic with the "humanizing the machine" concept, a multi-step registration flow with AI experience assessment, passwordless magic link authentication, and a course dashboard. The system includes a FastAPI backend with SQLite database for user management and experience tracking, plus a development-friendly localhost login for testing.

## User Story
As a prospective AI course student
I want to discover the course, register my interest with my AI experience level, authenticate securely via magic link, and access course materials
So that I can learn AI through structured sessions without the friction of password management while the instructor understands my current knowledge level

## Problem Statement
Creating an AI learning course requires a frictionless signup and authentication experience that captures student background information to tailor content appropriately. Traditional password-based authentication creates barriers to entry, while gathering experience data upfront enables personalized instruction. The platform needs to reflect the "humanizing the machine" philosophy through approachable design while providing robust user management for course access control.

## Solution Statement
Implement a modern, responsive web application with a branded landing page that guides users through a multi-step registration collecting AI experience data, authenticates them via passwordless magic link emails, stores user profiles and experience levels in SQLite, and provides authenticated access to a course dashboard. Include a development mode with quick user selection for localhost testing. The solution uses React + TypeScript + Tailwind CSS v4 + Shadcn UI on the frontend, FastAPI + SQLite on the backend, and follows the CrossGen AI visual identity with cyan/teal accents and dark gradients emphasizing approachability.

## Relevant Files
Use these files to implement the feature:

### Backend Files
- `app/server/main.py` - Register new authentication and user routes
- `app/server/core/config.py` - Add database, magic link, and environment configuration settings
- `app/server/models/schemas.py` - Define user, registration, and authentication request/response models
- `app/server/api/routes/health.py` - Reference for creating new route patterns
- `app_docs/patterns/backend-routes.md` - Pattern guide for creating API endpoints

### Frontend Files
- `app/client/src/App.tsx` - Configure routing for landing, registration, thank you, and course pages
- `app/client/src/components/layout/Layout.tsx` - Reference for responsive layout patterns
- `app/client/src/components/ui/button.tsx` - Shadcn button component
- `app/client/src/components/ui/card.tsx` - Shadcn card component for content organization
- `app/client/src/components/ui/input.tsx` - Shadcn input component for forms
- `app/client/src/components/ui/label.tsx` - Shadcn label component for forms
- `app/client/src/lib/api/client.ts` - Add API methods for registration, authentication, and user data
- `app/client/src/lib/api/types.ts` - Define TypeScript types for API responses
- `app/client/src/hooks/useHealth.ts` - Reference pattern for creating custom hooks
- `app_docs/patterns/frontend-hooks.md` - Pattern guide for creating React hooks
- `app/client/src/style.css` - Add CrossGen AI brand colors and custom theme variables

### Configuration Files
- `app/server/.env.sample` - Add database path, magic link service configuration, and email settings
- `README.md` - Reference for project structure and development workflow

### E2E Testing
- `.claude/commands/test_e2e.md` - E2E test execution instructions
- `.claude/commands/e2e/test_interest_form.md` - Reference example for E2E test structure

### New Files

#### Backend
- `app/server/db/__init__.py` - Database package initialization
- `app/server/db/database.py` - SQLite database connection and session management
- `app/server/db/models.py` - SQLAlchemy models for User and UserExperience tables
- `app/server/services/auth_service.py` - Magic link generation, validation, and authentication logic
- `app/server/services/user_service.py` - User creation, retrieval, and experience data management
- `app/server/api/routes/auth.py` - Authentication endpoints (magic link request, validation, localhost quick login)
- `app/server/api/routes/users.py` - User management endpoints (profile, experience data)
- `app/server/tests/test_auth.py` - Tests for authentication flows
- `app/server/tests/test_users.py` - Tests for user management

#### Frontend Pages
- `app/client/src/pages/LandingPage.tsx` - Landing page with CrossGen AI branding and course overview
- `app/client/src/pages/RegistrationPage.tsx` - Multi-step registration form with AI experience assessment
- `app/client/src/pages/ThankYouPage.tsx` - Post-registration page explaining magic link process
- `app/client/src/pages/LoginPage.tsx` - Magic link validation and localhost quick login
- `app/client/src/pages/CourseDashboard.tsx` - Authenticated course landing page
- `app/client/src/pages/AuthCallbackPage.tsx` - Magic link callback handler

#### Frontend Components
- `app/client/src/components/features/RegistrationForm.tsx` - Multi-step registration form component
- `app/client/src/components/features/ExperienceQuestions.tsx` - AI experience assessment questions
- `app/client/src/components/features/QuickLoginSelector.tsx` - Localhost user selection for development
- `app/client/src/components/features/Hero.tsx` - Landing page hero section
- `app/client/src/components/features/CourseOverview.tsx` - Course information section
- `app/client/src/components/ui/textarea.tsx` - Shadcn textarea component for experience questions
- `app/client/src/components/ui/select.tsx` - Shadcn select component for dropdowns
- `app/client/src/components/ui/progress.tsx` - Shadcn progress component for multi-step form

#### Frontend Hooks & Utils
- `app/client/src/hooks/useAuth.ts` - Authentication state management hook
- `app/client/src/hooks/useRegistration.ts` - Registration form state and submission hook
- `app/client/src/hooks/useUser.ts` - User data fetching hook
- `app/client/src/lib/auth.ts` - Authentication utilities and token management
- `app/client/src/types/user.ts` - User-related TypeScript types
- `app/client/src/types/auth.ts` - Authentication-related TypeScript types

#### E2E Test
- `.claude/commands/e2e/test_ai_course_signup_flow.md` - E2E test for complete registration and login flow

#### Database
- `app/server/ai_course.db` - SQLite database file (gitignored, created on first run)
- `app/server/migrations/init_db.py` - Database initialization script

## Implementation Plan

### Phase 1: Foundation
Establish the database layer, authentication infrastructure, and core backend services. Set up SQLite with SQLAlchemy models for users and experience data. Configure magic link authentication service using a third-party provider or custom JWT-based implementation. Add necessary configuration settings for database paths, email service, and authentication secrets. Create initial database migrations and setup scripts.

### Phase 2: Core Implementation
Implement backend API endpoints for user registration, magic link generation/validation, and user data retrieval. Build frontend pages for landing, registration (multi-step form with experience questions), thank you page, login (with magic link validation and localhost quick select), and course dashboard. Create reusable UI components for forms and authentication flows. Integrate CrossGen AI brand styling with cyan/teal primary colors and dark gradient backgrounds. Implement responsive layouts for mobile, tablet, and desktop.

### Phase 3: Integration
Connect frontend forms to backend APIs using custom hooks. Implement authentication state management and protected routes. Add localStorage token persistence for sessions. Integrate magic link email sending and callback handling. Create localhost development quick login with user selection dropdown. Add comprehensive error handling and loading states. Test full user journey from landing through registration, magic link authentication, to course dashboard access.

## Step by Step Tasks

### Task 1: Install Dependencies and Configure Database
- Run `cd app/server && uv add sqlalchemy alembic itsdangerous pyjwt` to add database and authentication dependencies
- Run `cd app/server && uv add python-multipart` for form handling
- Run `cd app/server && uv add aiosqlite` for async SQLite support
- Create `app/server/db/__init__.py`, `app/server/db/database.py`, and `app/server/db/models.py`
- Define SQLAlchemy User and UserExperience models with appropriate fields
- Implement database connection, session management, and table creation utilities
- Update `app/server/core/config.py` to add DATABASE_URL, SECRET_KEY, MAGIC_LINK_EXPIRY, and development mode settings

### Task 2: Implement Authentication Service
- Create `app/server/services/__init__.py` if it doesn't exist
- Create `app/server/services/auth_service.py` with functions for:
  - Generating magic link tokens (JWT-based with email and expiry)
  - Validating magic link tokens
  - Creating access tokens for authenticated sessions
  - Localhost quick login user selection
- Implement token signing/verification using `itsdangerous` or `pyjwt`
- Add configuration for token expiry times and secret keys

### Task 3: Implement User Service
- Create `app/server/services/user_service.py` with functions for:
  - Creating new users with email and name
  - Saving user experience data (questions and answers)
  - Retrieving user by ID or email
  - Listing all users (for localhost quick login)
  - Checking if user exists by email
- Implement database CRUD operations using SQLAlchemy sessions

### Task 4: Create Backend API Routes - Authentication
- Create `app/server/api/routes/auth.py` with endpoints:
  - `POST /api/auth/register` - Accept user registration data (name, email, experience responses)
  - `POST /api/auth/magic-link` - Generate and send magic link to user's email
  - `GET /api/auth/verify/{token}` - Validate magic link token and return access token
  - `GET /api/auth/localhost-users` - List all users for quick login (dev mode only)
  - `POST /api/auth/localhost-login` - Quick login by user ID (dev mode only)
- Follow patterns from `app_docs/patterns/backend-routes.md`
- Implement Pydantic models in `app/server/models/schemas.py` for all requests/responses
- Register router in `app/server/main.py`

### Task 5: Create Backend API Routes - Users
- Create `app/server/api/routes/users.py` with endpoints:
  - `GET /api/users/me` - Get current authenticated user profile
  - `GET /api/users/{user_id}` - Get user by ID (admin or self only)
  - `PUT /api/users/me` - Update user profile
  - `GET /api/users/me/experience` - Get user's experience data
- Implement authentication dependency using FastAPI `Depends`
- Register router in `app/server/main.py`

### Task 6: Write Backend Tests
- Create `app/server/tests/test_auth.py` to test:
  - User registration endpoint
  - Magic link generation
  - Token validation
  - Localhost quick login
- Create `app/server/tests/test_users.py` to test:
  - User profile retrieval
  - Experience data retrieval
  - User updates
- Follow patterns from `app/server/tests/test_health.py`
- Run `cd app/server && uv run pytest` to verify all tests pass

### Task 7: Install Frontend Dependencies and Configure Routing
- Run `cd app/client && bun add react-router-dom` for routing
- Run `cd app/client && bun add @tanstack/react-query` for data fetching (optional but recommended)
- Run `cd app/client && bunx shadcn@latest add textarea select progress` to add required Shadcn components
- Update `app/client/src/main.tsx` to include `BrowserRouter`
- Update `app/client/src/App.tsx` to configure routes for:
  - `/` - Landing page
  - `/register` - Registration page
  - `/thank-you` - Thank you page
  - `/login` - Login page
  - `/auth/callback` - Magic link callback handler
  - `/dashboard` - Course dashboard (protected route)

### Task 8: Create API Client Methods and Types
- Update `app/client/src/lib/api/types.ts` to define:
  - `User` interface (id, email, name, createdAt)
  - `UserExperience` interface (userId, questions, answers)
  - `RegistrationRequest` interface
  - `MagicLinkRequest` interface
  - `AuthResponse` interface
  - `LocalhostUser` interface for quick login
- Update `app/client/src/lib/api/client.ts` to add methods:
  - `register(data)` - POST registration
  - `requestMagicLink(email)` - POST magic link request
  - `verifyMagicLink(token)` - GET verify token
  - `getLocalhostUsers()` - GET localhost users list
  - `localhostLogin(userId)` - POST localhost login
  - `getCurrentUser()` - GET current user profile
  - `getUserExperience()` - GET user experience data

### Task 9: Create Authentication Hook and Utils
- Create `app/client/src/lib/auth.ts` with utilities:
  - `setToken(token)` - Store auth token in localStorage
  - `getToken()` - Retrieve auth token
  - `clearToken()` - Remove auth token
  - `isAuthenticated()` - Check if user has valid token
- Create `app/client/src/hooks/useAuth.ts` following patterns from `app_docs/patterns/frontend-hooks.md`:
  - Manage authentication state (user, loading, error)
  - Provide login, logout, and token validation functions
  - Auto-fetch user on mount if token exists
  - Return `{ user, loading, error, login, logout, isAuthenticated }`

### Task 10: Implement CrossGen AI Brand Styling
- Update `app/client/src/style.css` to add custom CSS variables:
  - Primary color: cyan/teal (rgba(6,182,212,0.8))
  - Background gradients: black to slate/zinc/neutral grays
  - Define dark theme defaults
  - Add gradient utility classes
- Create reusable gradient background styles
- Ensure all colors work with Tailwind v4 within `@layer base`

### Task 11: Create Landing Page Components
- Create `app/client/src/components/features/Hero.tsx`:
  - Large heading with "Humanizing the Machine" concept
  - Subheading explaining the AI course
  - Call-to-action button linking to `/register`
  - Use cyan/teal accents and dark gradient background
  - Fully responsive for mobile, tablet, desktop
- Create `app/client/src/components/features/CourseOverview.tsx`:
  - Display course benefits and schedule overview
  - Use Card components for modular information sections
  - Include upcoming session dates placeholder
- Create `app/client/src/pages/LandingPage.tsx`:
  - Compose Hero and CourseOverview components
  - Implement smooth scrolling sections
  - Add CrossGen AI logo (use placeholder or link to external asset)

### Task 12: Create Registration Page and Components
- Create `app/client/src/components/features/ExperienceQuestions.tsx`:
  - Multi-question form for AI experience assessment:
    - "What is your current level of AI experience?" (select: Beginner/Intermediate/Advanced)
    - "What are you hoping to learn from this course?" (textarea)
    - "Have you worked with AI tools before? If so, which ones?" (textarea)
  - Use Shadcn Input, Textarea, Select, and Label components
  - Return answers as structured data
- Create `app/client/src/components/features/RegistrationForm.tsx`:
  - Multi-step form with Progress indicator
  - Step 1: Name and Email inputs
  - Step 2: Experience Questions component
  - Step 3: Review and submit
  - Handle form state and validation
  - Submit to backend on completion
- Create `app/client/src/hooks/useRegistration.ts`:
  - Manage registration form state
  - Handle API submission
  - Return `{ registerUser, loading, error }`
- Create `app/client/src/pages/RegistrationPage.tsx`:
  - Render RegistrationForm
  - Navigate to `/thank-you` on success
  - Display errors appropriately
  - Responsive layout

### Task 13: Create Thank You and Login Pages
- Create `app/client/src/pages/ThankYouPage.tsx`:
  - Confirmation message for successful registration
  - Explain magic link process: "Check your email for a secure login link"
  - Provide next steps instructions
  - Link to login page for manual magic link entry (optional)
- Create `app/client/src/components/features/QuickLoginSelector.tsx`:
  - Dropdown showing list of registered users (localhost only)
  - "Quick Login" button
  - Only render if `import.meta.env.DEV` is true
  - Call `api.localhostLogin(userId)` on selection
- Create `app/client/src/pages/LoginPage.tsx`:
  - Show QuickLoginSelector in development mode
  - Input for manual magic link token entry (optional)
  - Handle authentication and redirect to `/dashboard`
  - Display loading and error states
- Create `app/client/src/pages/AuthCallbackPage.tsx`:
  - Extract token from URL query params (`?token=...`)
  - Call `api.verifyMagicLink(token)`
  - Store returned auth token using `setToken()`
  - Redirect to `/dashboard` on success
  - Show error message on failure

### Task 14: Create Course Dashboard Page
- Create `app/client/src/pages/CourseDashboard.tsx`:
  - Welcome message with user's name
  - Placeholder sections for:
    - Upcoming sessions
    - Course materials (to be implemented)
    - User progress
  - Logout button
  - Use Card components for content organization
  - Fully responsive layout
- Create `app/client/src/hooks/useUser.ts`:
  - Fetch current user data
  - Return `{ user, loading, error, refetch }`
  - Follow patterns from `app_docs/patterns/frontend-hooks.md`

### Task 15: Implement Protected Routes
- Create `app/client/src/components/layout/ProtectedRoute.tsx`:
  - Wrapper component that checks authentication
  - Redirect to `/login` if not authenticated
  - Show loading spinner while checking auth status
  - Use `useAuth` hook
- Update `app/client/src/App.tsx`:
  - Wrap `/dashboard` route with ProtectedRoute
  - Ensure other routes are publicly accessible

### Task 16: Create E2E Test File
- Create `.claude/commands/e2e/test_ai_course_signup_flow.md` with:
  - **User Story**: Test complete registration and login flow
  - **Test Steps**:
    1. Navigate to landing page
    2. Verify hero section and call-to-action
    3. Click "Sign Up" button
    4. Fill out registration form (all steps)
    5. Submit registration
    6. Verify thank you page displays
    7. Navigate to login page
    8. Use localhost quick login (dev mode)
    9. Verify redirect to course dashboard
    10. Verify user name displays on dashboard
    11. Click logout
    12. Verify redirect to landing page
  - **Success Criteria**:
    - All form inputs accept data
    - Registration submits successfully
    - Quick login works in dev mode
    - Dashboard displays user information
    - Logout redirects properly
  - Include screenshot capture points at each major step
  - Follow format from `.claude/commands/e2e/test_interest_form.md`

### Task 17: Database Initialization
- Create `app/server/migrations/init_db.py`:
  - Script to create all tables on first run
  - Check if tables exist before creating
  - Optionally seed with test users for development
- Update `app/server/server.py` or `app/server/main.py`:
  - Add startup event to initialize database
  - Call table creation on app startup
- Add `app/server/ai_course.db` to `.gitignore`

### Task 18: Integration Testing and Bug Fixes
- Start both frontend and backend: `./scripts/start.sh`
- Manually test complete user flow:
  - Landing page loads with proper styling
  - Registration form accepts input and validates
  - Thank you page displays after submission
  - Localhost quick login works (verify database writes)
  - Dashboard shows user data correctly
  - Logout clears session and redirects
- Fix any bugs encountered during manual testing
- Ensure responsive design works on mobile viewport
- Test CORS configuration for API calls

### Task 19: Run All Validation Commands
- Execute all validation commands from the `Validation Commands` section below
- Ensure zero errors and zero regressions
- Fix any issues that arise
- Re-run commands until all pass

## Testing Strategy

### Unit Tests

**Backend Tests:**
- `app/server/tests/test_auth.py`:
  - Test user registration with valid data
  - Test duplicate email rejection
  - Test magic link token generation
  - Test token validation (valid and expired tokens)
  - Test localhost quick login
  - Test authentication with invalid tokens

- `app/server/tests/test_users.py`:
  - Test retrieving current user profile
  - Test retrieving user by ID
  - Test updating user profile
  - Test retrieving user experience data
  - Test unauthorized access to user endpoints

**Frontend Tests:**
- Component tests for key UI components
- Hook tests for `useAuth`, `useRegistration`, `useUser`
- API client method tests (mocked)

### Edge Cases
- Empty form submission (should show validation errors)
- Invalid email format in registration
- Expired magic link token (should show error message)
- Accessing protected routes without authentication (should redirect to login)
- Duplicate user registration (should show "Email already registered" error)
- Network failures during API calls (should show user-friendly error messages)
- Very long text in experience questions (should handle gracefully with max length)
- Quick login when no users exist (should show "No users available")
- Token storage when localStorage is unavailable (should handle gracefully)
- Mobile viewport testing for all form interactions
- Magic link in different browsers (test token passing)
- Logout while on protected page (should redirect immediately)

## Acceptance Criteria
1. Landing page displays with CrossGen AI branding (cyan/teal primary color, dark gradients) and clear call-to-action
2. Registration form collects name, email, and AI experience data through multi-step process with progress indicator
3. Thank you page explains magic link authentication clearly
4. Magic link tokens are generated and can be validated (email sending can be stubbed for MVP)
5. Localhost quick login displays list of users and authenticates without magic link in development mode
6. Course dashboard displays after successful authentication and shows user's name
7. Protected routes redirect unauthenticated users to login page
8. Logout functionality clears session and redirects to landing page
9. All pages are fully responsive on mobile (375px), tablet (768px), and desktop (1024px+) viewports
10. SQLite database correctly stores users and experience data
11. All backend tests pass with zero failures
12. Frontend builds without TypeScript errors
13. E2E test validates complete signup and login flow with screenshots

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_ai_course_signup_flow.md` to validate the complete signup and authentication flow works end-to-end with visual confirmation
- `cd app/server && uv run pytest -v` - Run all backend tests including new auth and user tests (must pass with zero failures)
- `cd app/client && bun run tsc --noEmit` - Run TypeScript type checking on frontend (must complete with zero errors)
- `cd app/client && bun run build` - Build frontend for production (must complete successfully)
- `cd app/server && uv run ruff check .` - Lint backend code (should have minimal warnings)
- Manual verification checklist:
  - Visit `http://localhost:5173/` and verify landing page displays with CrossGen AI styling
  - Navigate through registration form and verify all steps work
  - Submit registration and verify thank you page displays
  - Verify user is saved in database (`app/server/ai_course.db`)
  - Use localhost quick login and verify redirect to dashboard
  - Verify dashboard displays user name from database
  - Click logout and verify redirect to landing page
  - Test responsive design by resizing browser to mobile width (375px)
  - Verify protected route (`/dashboard`) redirects to login when not authenticated

## Notes
- **Magic Link Email**: For MVP, focus on generating and validating tokens. Email sending can be stubbed or implemented with a simple SMTP service (like Mailgun/SendGrid). In development, tokens can be logged to console for testing.
- **Database Migrations**: Using raw SQLAlchemy table creation for MVP. Consider adding Alembic migrations for production version to handle schema changes.
- **Authentication Security**: Use strong SECRET_KEY in production (from environment variable). Implement token expiry checking. Consider adding refresh tokens for longer sessions.
- **Localhost Quick Login**: Only available in development mode (`SERVER_RELOAD=True` or similar flag). Never expose in production.
- **CrossGen AI Assets**: Logo and specific brand assets should be provided by the user or linked from the main CrossGen AI website. Use placeholder if not available.
- **Future Enhancements**:
  - Payment integration for course fees
  - Course material upload and management
  - Session scheduling and calendar integration
  - Email notifications for upcoming sessions
  - Admin dashboard for managing users and content
  - Analytics for tracking user engagement
- **Libraries Added**:
  - Backend: `sqlalchemy`, `alembic`, `itsdangerous`, `pyjwt`, `python-multipart`, `aiosqlite`
  - Frontend: `react-router-dom`, `@tanstack/react-query` (optional), Shadcn components: `textarea`, `select`, `progress`
- **Environment Variables**: Add to `app/server/.env`:
  - `DATABASE_URL=sqlite:///./ai_course.db`
  - `SECRET_KEY=<generate-secure-random-key>`
  - `MAGIC_LINK_EXPIRY=3600` (1 hour in seconds)
  - `EMAIL_SERVICE_API_KEY=<if-using-email-service>`
  - `DEVELOPMENT_MODE=True` (for localhost quick login)
