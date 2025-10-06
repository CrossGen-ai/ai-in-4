# Feature: AI Course Platform MVP

## Metadata
issue_number: `7`
adw_id: `3e81e604`
issue_json: `{"number":7,"title":"Framework","body":"adw_plan_build_test_review\n\nWe are creating a web site course for teaching people to learn AI. I will be hosting learning sessions. This website is for signing up and paying for it as well as where to go to to get course materials after I'm done as well as the future upcoming schedule. It will be at: ai-in-4.crossgen-ai.com sub domain.\n\nInitial MVP:\n\nLanding page (react, tailwindscss, shadcn) follow the styling of [www.crossgen-ai.com](http://www.crossgen-ai.com/) (logo and themes). Keep the idea of \"humanizing the machine\" from the website\na registration page - sign up\nregiraiton page should ingerview about their AI experiance and save the results. to a user experience table\nFast API backend. Use magiclink for signup\nSQLlite database\nfor fast log in with localhost by selecting a user to logon as and auto log in as that user.\nthere should be a thank you registration page explaining magic link\nthe login should go to a basic \"course\" landing page we will build out\nkeep all design responsive for mobile, tablet, and desktop"}`

## Feature Description
This feature implements the foundational MVP for an AI course platform where users can register for learning sessions, pay for courses, access course materials, and view upcoming schedules. The platform includes a magic link authentication system, user experience profiling during registration, and a course landing page accessible after login. The design follows the CrossGen AI brand identity with responsive layouts across mobile, tablet, and desktop devices.

## User Story
As a prospective AI student
I want to register for AI learning sessions using a simple magic link authentication system
So that I can securely access course materials and upcoming schedules without managing passwords

## Problem Statement
There is currently no dedicated platform for the AI course offering. Users need a streamlined way to:
- Discover and register for AI learning sessions
- Complete an experience assessment to enable personalized learning paths
- Authenticate securely without password management
- Access course materials and schedule information after registration

## Solution Statement
Build a full-stack web application with:
- A branded landing page following CrossGen AI's "humanizing the machine" theme
- Magic link authentication for passwordless signup/login
- User experience assessment integrated into the registration flow
- SQLite database for storing user data and experience profiles
- A localhost development mode with quick user selection for testing
- Responsive design for all device sizes
- A course landing page for authenticated users

## Relevant Files

### Backend Files
- `app/server/core/config.py` - Add database configuration, magic link settings, SMTP configuration for email sending
- `app/server/main.py` - Register new authentication and user routes
- `app/server/models/schemas.py` - Define Pydantic models for User, UserExperience, MagicLink, Course schemas
- `app/server/api/routes/auth.py` - NEW: Magic link generation, validation, login/logout endpoints
- `app/server/api/routes/users.py` - NEW: User registration, profile management, experience assessment endpoints
- `app/server/api/routes/courses.py` - NEW: Course listing and materials access endpoints
- `app/server/db/database.py` - NEW: SQLite database connection and session management
- `app/server/db/models.py` - NEW: SQLAlchemy ORM models for User, UserExperience, MagicLink, Course tables
- `app/server/services/magic_link.py` - NEW: Magic link generation, validation, and email sending logic
- `app/server/services/user_service.py` - NEW: User creation, authentication, and experience profile management
- `app/server/tests/test_auth.py` - NEW: Tests for authentication endpoints
- `app/server/tests/test_users.py` - NEW: Tests for user management endpoints

### Frontend Files
- `app/client/src/App.tsx` - Update routing to include landing, registration, login, thank-you, and course pages
- `app/client/src/pages/Landing.tsx` - NEW: Landing page with CrossGen AI branding
- `app/client/src/pages/Register.tsx` - NEW: Registration page with experience assessment form
- `app/client/src/pages/ThankYou.tsx` - NEW: Thank you page explaining magic link process
- `app/client/src/pages/Login.tsx` - NEW: Login page and magic link validation handler
- `app/client/src/pages/DevLogin.tsx` - NEW: Localhost development quick login page
- `app/client/src/pages/CourseLanding.tsx` - NEW: Authenticated course landing page
- `app/client/src/components/layout/Header.tsx` - NEW: Header component with navigation
- `app/client/src/components/layout/Footer.tsx` - NEW: Footer component
- `app/client/src/components/auth/ProtectedRoute.tsx` - NEW: Route guard for authenticated pages
- `app/client/src/hooks/useAuth.ts` - NEW: Authentication state management hook
- `app/client/src/hooks/useUser.ts` - NEW: User profile data hook
- `app/client/src/lib/api/client.ts` - Add authentication, user, and course API methods
- `app/client/src/lib/api/types.ts` - Define TypeScript types for User, UserExperience, Course, AuthResponse
- `app/client/src/context/AuthContext.tsx` - NEW: React context for global authentication state
- `app/client/src/style.css` - Update with CrossGen AI brand colors and theme variables

### Database Files
- `app/server/db/init.sql` - NEW: Initial database schema SQL script
- `app/server/db/seed.sql` - NEW: Seed data for development (sample users, courses)

### Configuration Files
- `app/server/.env.sample` - Add DATABASE_URL, MAGIC_LINK_SECRET, EMAIL_HOST, EMAIL_PORT, EMAIL_FROM, FRONTEND_URL variables
- `.sample.env` - Update to include any root-level configuration if needed

### New Files

#### E2E Test
- `.claude/commands/e2e/test_registration_flow.md` - E2E test to validate the complete registration and magic link authentication flow

## Implementation Plan

### Phase 1: Foundation
1. Set up SQLite database schema and connection layer
2. Configure environment variables for database, magic link secrets, and email (SMTP)
3. Create SQLAlchemy ORM models for User, UserExperience, MagicLink, Course
4. Add required Python dependencies: `sqlalchemy`, `aiosqlite`, `passlib`, `python-multipart`, `pydantic[email]`, `itsdangerous`
5. Set up database initialization and migration scripts
6. Create authentication context and protected route components on frontend
7. Define TypeScript types for all API entities

### Phase 2: Core Implementation
1. Implement magic link service (generation, validation, email sending)
2. Build authentication API endpoints (generate magic link, validate token, login, logout)
3. Build user management API endpoints (registration with experience assessment, profile retrieval)
4. Create course API endpoints (list courses, get course details)
5. Build landing page with CrossGen AI branding
6. Build registration page with experience assessment form
7. Build thank you page with magic link explanation
8. Build login page and magic link validation handler
9. Build localhost development quick login page
10. Build course landing page for authenticated users
11. Implement authentication hooks and context
12. Add responsive styling using Tailwind v4 and CrossGen AI theme

### Phase 3: Integration
1. Connect frontend registration flow to backend API
2. Connect magic link authentication flow end-to-end
3. Integrate protected routes with authentication state
4. Connect course landing page to course API
5. Test responsive design across mobile, tablet, desktop
6. Validate magic link email delivery (or console logging in dev mode)
7. Create seed data for development testing

## Step by Step Tasks

### Task 1: Database Setup
- Create `app/server/db/database.py` with SQLite connection using SQLAlchemy async engine
- Create `app/server/db/models.py` with ORM models:
  - `User` (id, email, created_at, last_login, is_active)
  - `UserExperience` (id, user_id, experience_level, background, goals, created_at)
  - `MagicLink` (id, user_id, token, expires_at, created_at, used)
  - `Course` (id, title, description, schedule, materials_url, created_at)
- Create `app/server/db/init.sql` with table creation SQL
- Create `app/server/db/seed.sql` with sample development data
- Add database configuration to `app/server/core/config.py` (DATABASE_URL, connection settings)
- Add dependencies: `uv add sqlalchemy aiosqlite alembic`

### Task 2: Pydantic Schemas
- Update `app/server/models/schemas.py` with models:
  - `UserCreate` (email, experience_level, background, goals)
  - `UserResponse` (id, email, created_at, last_login)
  - `UserExperienceCreate` (experience_level, background, goals)
  - `UserExperienceResponse` (id, user_id, experience_level, background, goals, created_at)
  - `MagicLinkRequest` (email)
  - `MagicLinkValidate` (token)
  - `AuthResponse` (access_token, user: UserResponse)
  - `CourseResponse` (id, title, description, schedule, materials_url)

### Task 3: Magic Link Service
- Create `app/server/services/magic_link.py` with functions:
  - `generate_magic_link(email: str, db: Session) -> str` - Create token, save to database, return magic link URL
  - `validate_magic_link(token: str, db: Session) -> User | None` - Validate token, mark as used, return user
  - `send_magic_link_email(email: str, magic_link: str)` - Send email (or log to console in dev mode)
- Add dependencies: `uv add itsdangerous python-multipart`
- Add configuration to `app/server/core/config.py`: MAGIC_LINK_SECRET, MAGIC_LINK_EXPIRY_MINUTES, EMAIL_HOST, EMAIL_PORT, EMAIL_FROM, FRONTEND_URL

### Task 4: User Service
- Create `app/server/services/user_service.py` with functions:
  - `create_user(user_data: UserCreate, db: Session) -> User` - Create user and associated experience profile
  - `get_user_by_email(email: str, db: Session) -> User | None`
  - `get_user_by_id(user_id: int, db: Session) -> User | None`
  - `update_last_login(user_id: int, db: Session)`
  - `get_user_experience(user_id: int, db: Session) -> UserExperience | None`
- Write unit tests in `app/server/tests/test_user_service.py`

### Task 5: Authentication Routes
- Create `app/server/api/routes/auth.py` with endpoints:
  - `POST /api/auth/register` - Create user with experience assessment, send magic link
  - `POST /api/auth/magic-link` - Generate and send magic link for existing user
  - `POST /api/auth/validate` - Validate magic link token and return auth response
  - `POST /api/auth/logout` - Logout (clear session/token)
  - `GET /api/auth/dev-users` - List users for localhost quick login (only in dev mode)
- Register router in `app/server/main.py`
- Write tests in `app/server/tests/test_auth.py`

### Task 6: User Management Routes
- Create `app/server/api/routes/users.py` with endpoints:
  - `GET /api/users/me` - Get current user profile
  - `GET /api/users/me/experience` - Get user experience profile
- Register router in `app/server/main.py`
- Write tests in `app/server/tests/test_users.py`

### Task 7: Course Routes
- Create `app/server/api/routes/courses.py` with endpoints:
  - `GET /api/courses` - List all available courses
  - `GET /api/courses/{course_id}` - Get course details
- Register router in `app/server/main.py`
- Write tests in `app/server/tests/test_courses.py`

### Task 8: Frontend TypeScript Types
- Update `app/client/src/lib/api/types.ts` with interfaces:
  - `User` (id, email, createdAt, lastLogin)
  - `UserExperience` (id, userId, experienceLevel, background, goals, createdAt)
  - `UserCreate` (email, experienceLevel, background, goals)
  - `MagicLinkRequest` (email)
  - `AuthResponse` (accessToken, user: User)
  - `Course` (id, title, description, schedule, materialsUrl)

### Task 9: API Client Methods
- Update `app/client/src/lib/api/client.ts` with methods:
  - `auth.register(data: UserCreate)` - Register user
  - `auth.requestMagicLink(email: string)` - Request magic link
  - `auth.validateMagicLink(token: string)` - Validate magic link token
  - `auth.logout()` - Logout
  - `auth.getDevUsers()` - Get dev users for quick login
  - `users.getCurrentUser()` - Get current user
  - `users.getUserExperience()` - Get user experience
  - `courses.listCourses()` - List courses
  - `courses.getCourse(id: number)` - Get course by ID

### Task 10: Authentication Context
- Create `app/client/src/context/AuthContext.tsx` with:
  - Context provider for global auth state (user, isAuthenticated, loading)
  - Functions: login, logout, validateToken
  - Local storage for token persistence
- Create `app/client/src/hooks/useAuth.ts` hook to consume auth context

### Task 11: User Hooks
- Create `app/client/src/hooks/useUser.ts` for fetching current user and experience data

### Task 12: Protected Route Component
- Create `app/client/src/components/auth/ProtectedRoute.tsx` that redirects to login if not authenticated

### Task 13: Update Styling with Brand Theme
- Update `app/client/src/style.css` with CrossGen AI brand colors:
  - Primary color scheme matching www.crossgen-ai.com
  - Typography following brand guidelines
  - Responsive breakpoints for mobile, tablet, desktop
  - CSS variables for "humanizing the machine" theme

### Task 14: Header and Footer Components
- Create `app/client/src/components/layout/Header.tsx` with navigation, logo, responsive menu
- Create `app/client/src/components/layout/Footer.tsx` with branding and links
- Update `app/client/src/components/layout/Layout.tsx` to include Header and Footer

### Task 15: Landing Page
- Create `app/client/src/pages/Landing.tsx`:
  - Hero section with "humanizing the machine" messaging
  - Call-to-action to register
  - Course highlights
  - Responsive design following CrossGen AI branding
  - Navigation to registration page

### Task 16: Registration Page
- Create `app/client/src/pages/Register.tsx`:
  - Email input field
  - Experience level dropdown/radio (Beginner, Intermediate, Advanced)
  - Background text area (tell us about your background)
  - Goals text area (what do you hope to achieve?)
  - Submit button
  - Form validation
  - On submit: call `auth.register()`, redirect to thank you page

### Task 17: Thank You Page
- Create `app/client/src/pages/ThankYou.tsx`:
  - Explain magic link authentication
  - Instruct user to check email
  - Provide context about the login process
  - Responsive design

### Task 18: Login Page
- Create `app/client/src/pages/Login.tsx`:
  - Email input field with "Send Magic Link" button
  - Magic link validation handler (reads token from URL query params)
  - On successful validation: save token, redirect to course landing
  - Error handling for expired/invalid tokens

### Task 19: Dev Login Page
- Create `app/client/src/pages/DevLogin.tsx`:
  - Only accessible in development mode
  - List of users from `auth.getDevUsers()`
  - Click on user to auto-login as that user
  - Redirect to course landing after selection

### Task 20: Course Landing Page
- Create `app/client/src/pages/CourseLanding.tsx`:
  - Display welcome message with user name/email
  - List upcoming courses using `courses.listCourses()`
  - Course materials access links
  - Schedule overview
  - Logout button
  - Protected with `ProtectedRoute`

### Task 21: Update App Routing
- Update `app/client/src/App.tsx` to include routes:
  - `/` - Landing page
  - `/register` - Registration page
  - `/thank-you` - Thank you page
  - `/login` - Login page
  - `/dev-login` - Dev login page (only in dev mode)
  - `/courses` - Course landing page (protected)
- Install React Router: `cd app/client && yarn add react-router-dom`

### Task 22: Create E2E Test
- Create `.claude/commands/e2e/test_registration_flow.md` following the pattern from `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_interest_form.md`
- Test steps should cover:
  1. Navigate to landing page
  2. Click register button
  3. Fill registration form with experience assessment
  4. Submit registration
  5. Verify thank you page displays
  6. (For dev mode) Navigate to dev login
  7. Select user and auto-login
  8. Verify course landing page loads
  9. Verify user info displays correctly
- Capture screenshots at each major step

### Task 23: Database Initialization Script
- Create script `app/server/db/init_db.py` to initialize database and run migrations
- Run database initialization: `cd app/server && uv run python db/init_db.py`

### Task 24: Seed Development Data
- Create script `app/server/db/seed_db.py` to populate database with sample users and courses
- Run seed script: `cd app/server && uv run python db/seed_db.py`

### Task 25: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Testing Strategy

### Unit Tests

#### Backend Tests
- **Authentication Service Tests** (`test_auth.py`):
  - Test magic link generation creates valid token
  - Test magic link validation succeeds with valid token
  - Test magic link validation fails with expired token
  - Test magic link validation fails with used token
  - Test user registration creates user and experience profile

- **User Service Tests** (`test_user_service.py`):
  - Test create user with experience profile
  - Test get user by email
  - Test get user by ID
  - Test update last login timestamp
  - Test get user experience profile

- **API Route Tests**:
  - Test registration endpoint creates user and sends magic link
  - Test magic link request endpoint for existing users
  - Test validate endpoint with valid/invalid tokens
  - Test protected user endpoints require authentication
  - Test course listing endpoint returns courses

#### Frontend Tests
- **Hook Tests**:
  - Test `useAuth` hook manages auth state correctly
  - Test `useUser` hook fetches user data

- **Component Tests**:
  - Test registration form validation
  - Test protected route redirects unauthenticated users
  - Test login form handles magic link validation

### Edge Cases
- Empty email in registration/login forms
- Invalid email format
- Expired magic link tokens
- Already used magic link tokens
- Non-existent user requesting magic link
- Duplicate user registration attempts
- Network errors during API calls
- Missing or invalid authentication tokens for protected routes
- Rapid repeated magic link requests (rate limiting consideration)
- Browser back button after logout
- Token expiry while user is on course page
- Mobile/tablet responsive breakpoints
- Very long text in experience assessment fields

## Acceptance Criteria
- [ ] User can view landing page with CrossGen AI branding on all device sizes
- [ ] User can complete registration with email and experience assessment
- [ ] Registration creates user record and experience profile in database
- [ ] Magic link is generated and sent (or logged in dev mode) after registration
- [ ] Thank you page explains magic link process clearly
- [ ] User can click magic link in email to authenticate
- [ ] Magic link validation logs user in and redirects to course landing page
- [ ] Authenticated users can view course landing page with courses and materials
- [ ] Users can logout successfully
- [ ] Dev mode allows quick login by selecting a user from list
- [ ] Protected routes redirect to login when unauthenticated
- [ ] All pages are responsive across mobile, tablet, and desktop
- [ ] Database stores users, experience profiles, magic links, and courses correctly
- [ ] All API endpoints return appropriate status codes and error messages
- [ ] Frontend displays user-friendly error messages for failed operations
- [ ] Theme follows CrossGen AI brand identity ("humanizing the machine")

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

1. Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_registration_flow.md` to validate the registration and authentication flow works end-to-end.
2. `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
3. `cd app/client && bun run type-check` - Run frontend type checking to validate the feature works with zero regressions
4. `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions
5. Manual verification:
   - Start application with `./scripts/start.sh`
   - Navigate to landing page and verify branding matches CrossGen AI
   - Complete registration flow with experience assessment
   - Verify magic link is generated (check console logs in dev mode)
   - Use dev login to authenticate as a test user
   - Verify course landing page loads and displays user info
   - Test responsive design on mobile, tablet, desktop viewports
   - Verify logout works and redirects to landing page

## Notes

### Dependencies to Add
Run these commands to add required backend dependencies:
```bash
cd app/server
uv add sqlalchemy aiosqlite alembic itsdangerous python-multipart pydantic[email]
```

Run these commands to add required frontend dependencies:
```bash
cd app/client
yarn add react-router-dom
yarn add -D @types/react-router-dom
```

### Environment Variables
Update `app/server/.env.sample` with:
```
DATABASE_URL=sqlite+aiosqlite:///./app.db
MAGIC_LINK_SECRET=your-secret-key-change-in-production
MAGIC_LINK_EXPIRY_MINUTES=15
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_FROM=noreply@crossgen-ai.com
FRONTEND_URL=http://localhost:5173
```

For localhost development, magic link emails should be logged to console instead of sent via SMTP.

### Design Considerations
- Follow CrossGen AI website (www.crossgen-ai.com) for color palette, typography, and "humanizing the machine" theme
- Ensure all forms have proper validation and user-friendly error messages
- Use Tailwind v4 utility classes for responsive design
- Leverage Shadcn UI components for consistent styling
- Maintain accessibility standards (ARIA labels, keyboard navigation)

### Security Considerations
- Magic links expire after configured time (default 15 minutes)
- Magic links can only be used once
- Tokens should be cryptographically secure (using `itsdangerous` library)
- Email addresses should be validated and sanitized
- CORS should be configured to only allow frontend URL
- In production, use environment variables for all secrets
- Consider rate limiting for magic link generation endpoints

### Future Enhancements (Out of Scope for MVP)
- Payment integration for course fees
- Course progress tracking
- Admin panel for course management
- Email templates with branding
- Password recovery flow
- User profile editing
- Course completion certificates
- Social login options (Google, GitHub)
