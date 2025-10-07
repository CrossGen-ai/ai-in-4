# Feature: Extended Interview Registration Form

## Metadata
issue_number: `11`
adw_id: `75b2208e`
issue_json: `{"number":11,"title":"extended interview","body":"adw_plan_build_test_review\n\nAdjust the registrartion page to a bigger Q&A.  \n\nBasic Info\n\nName: [Open-ended text, 100 char limit]\nEmail: [Email validation, 150 char limit]\nEmployment Status: [Single select dropdown]\n\nEmployed full-time\nEmployed part-time\nSelf-employed/Freelancer\nBetween jobs\nHomemaker\nRetired\nStudent\nOther: [If selected, show text field, 50 char limit]\n\n\nIndustry/Field (if applicable): [Open-ended text, 100 char limit, optional]\nRole/Job Title (if applicable): [Open-ended text, 100 char limit, optional]\n\nPrimary Use Context\n\nWhere do you plan to use AI most? [Single select radio buttons]\n\nWork/Professional tasks\nHome/Personal use\nBoth equally\nEducational purposes\nSide business/Hobby projects\n\n\n\nCurrent AI Experience\n\nHave you tried AI tools before? [Yes/No toggle or radio buttons]\nWhich AI tools have you used? [Multi-select checkboxes, conditional: only show if \"Yes\" above]\n\nChatGPT\nClaude\nGrok\nGemini\nPerplexity\nCopilot (Microsoft)\nMidjourney/DALL-E (image generation)\nOther: [If checked, show text field, 100 char limit]\n\n\n\nUsage & Comfort Level\n\nHow often do you currently use AI tools? [Single select dropdown or radio buttons]\n\nNever\nOnce a month or less\nWeekly\nDaily\nMultiple times per day\n\n\nRate your comfort level with AI: [Single select slider or radio buttons, 1-5 scale]\n\n1 = Complete beginner\n2 = Slightly familiar\n3 = Somewhat comfortable\n4 = Confident\n5 = Very confident\n\n\n\nGoals & Applications\n\nWhat do you want to use AI for? [Multi-select checkboxes, limit to 3 selections, show counter]\n\nWriting/content creation\nResearch and information gathering\nData analysis\nCoding/technical tasks\nCreative work (images, design)\nCustomer service/communication\nProcess automation\nLearning new skills\nPersonal productivity/organization\nMeal planning/household management\nCareer transition support\nOther: [If checked, show text field, 100 char limit]\n\n\n\nBiggest Challenge\n\nWhat's your biggest obstacle with AI right now? [Multi-select checkboxes, no limit]\n\nDon't know where to start\nUnderstanding what AI can/can't do\nWriting effective prompts\nKnowing which tool to use when\nIntegrating AI into my workflow\nConcerns about accuracy/reliability\nPrivacy/security concerns\nCost of AI tools\nOther: [If checked, show text field, 150 char limit]\n\n\n\nLearning Preference\n\nHow do you learn best? [Single select radio buttons]\n\nStep-by-step tutorials\nWatching video demonstrations\nHands-on practice with examples\nReading documentation\nMix of all above\n\n\nIs there anything else you'd like us to know about your AI learning goals? [Optional open-ended text area, 500 char limit]\n\n--------------\nTechnical Implementation Notes:\n\nRequired fields: Name, Email, Employment Status, Have you tried AI before, Primary Use Context, Comfort Level, Goals (must select 3), Learning Preference\nOptional fields: Industry/Field, Role/Job Title, Additional Comments\nConditional logic: AI tools question only appears if \"Yes\" to tried AI before\nValidation: Email format, character limits enforced\nProgress indicator: Show \"Step X of Y\" if breaking into multiple pages\nSave progress: Consider allowing users to save and return later"}`

## Feature Description
Expand the current registration form from a simple 4-field form (email, experience level, background, goals) into a comprehensive multi-section interview questionnaire that captures detailed information about new users' employment status, AI experience, usage patterns, learning goals, and challenges. This enhanced form will enable better personalization of the learning experience and more targeted course recommendations.

The new form includes:
- Basic personal/professional information (name, email, employment status, industry/role)
- Primary AI use context (work, home, educational, etc.)
- Current AI experience assessment (tools used, frequency, comfort level)
- Goals and applications (multi-select with 3-item limit)
- Biggest challenges with AI (multi-select, unlimited)
- Learning preference assessment
- Optional free-text feedback section

The form implements conditional logic (AI tools question only appears if user has tried AI before), character limits, validation, and maintains all existing magic link authentication functionality.

## User Story
As a prospective AI learning platform user
I want to provide detailed information about my background, AI experience, and learning goals during registration
So that the platform can personalize my learning experience and recommend the most relevant courses for my needs

## Problem Statement
The current registration form only captures minimal information (email, experience level, background, goals) which limits the platform's ability to:
1. Understand user demographics and professional contexts
2. Assess actual AI tool experience vs. self-reported comfort levels
3. Identify specific use cases and applications users are interested in
4. Tailor course content and recommendations to individual needs
5. Track common challenges to improve course design
6. Match learning delivery methods to user preferences

This lack of detailed onboarding data results in a generic learning experience that doesn't leverage user context for personalization.

## Solution Statement
Replace the simple 4-field registration form with a comprehensive multi-section interview form that systematically captures:
1. Professional context (employment, industry, role) to understand user backgrounds
2. Primary use context to align course examples with real-world applications
3. Detailed AI experience data (specific tools, frequency, comfort) for accurate skill assessment
4. Multi-select goals with enforced prioritization (3-item limit) to focus learning paths
5. Challenge identification to proactively address pain points
6. Learning preference data to optimize content delivery format

The solution maintains the existing UX flow (registration → magic link → courses) while significantly expanding the data collected. Implementation uses conditional rendering, client-side validation, and progressive disclosure to keep the form approachable despite its length.

## Relevant Files
Use these files to implement the feature:

- **app/client/src/pages/Register.tsx** - Current registration form component that needs to be expanded with all new fields and sections
- **app/client/src/pages/Register.test.tsx** - Existing test suite that needs comprehensive updates to cover all new form fields, conditional logic, validation rules, and multi-select behavior
- **app/server/models/schemas.py** - Pydantic schemas for request/response validation; needs new `UserCreate` schema with all additional fields
- **app/server/db/models.py** - SQLAlchemy database models; needs new `UserProfile` or extended `UserExperience` model to store the additional registration data
- **app/server/api/routes/auth.py** - Registration endpoint that processes the form submission; needs to handle expanded user data
- **app/server/services/user_service.py** - User creation service logic; needs to create/update profile records with new data
- **app/client/src/lib/api/types.ts** - TypeScript type definitions for API requests/responses; needs updated `UserCreate` interface
- **app/client/src/lib/api/client.ts** - API client methods; register method already exists, just needs to handle expanded payload
- **app_docs/patterns/backend-routes.md** - Reference for FastAPI route patterns
- **app_docs/patterns/frontend-hooks.md** - Reference for React hooks if needed for form state management
- **.claude/commands/test_e2e.md** - E2E test runner documentation
- **.claude/commands/e2e/test_registration_flow.md** - Existing registration E2E test that will need updates

### New Files
- **app/server/tests/test_registration_extended.py** - New test file for backend validation of extended registration data
- **.claude/commands/e2e/test_extended_registration_form.md** - New E2E test specification for the extended registration form functionality

## Implementation Plan

### Phase 1: Foundation
Update database schema and backend models to support all new registration fields. This includes creating/modifying database tables to store:
- Basic info (name, employment status, industry, role)
- Primary use context
- AI experience data (tried before flag, tools used array, usage frequency, comfort level)
- Goals array (with validation for max 3 selections)
- Challenges array (unlimited selections)
- Learning preference
- Additional comments

Update Pydantic schemas for request validation and response serialization. Modify the user creation service to handle the expanded data model and ensure proper storage.

### Phase 2: Core Implementation
Rebuild the frontend registration form with all new sections and fields:
- Implement multi-section layout with clear visual grouping
- Add conditional rendering for AI tools question (only shows if "tried before" is Yes)
- Implement multi-select checkboxes with 3-item limit enforcement for Goals section
- Add character limit validation for all text inputs
- Create responsive, accessible form controls (dropdowns, radio buttons, checkboxes, text areas)
- Maintain existing error handling and loading states
- Preserve navigation flow (Register → Thank You → Courses)

### Phase 3: Integration
Update API client types and ensure seamless data flow from frontend form through API to database. Update existing tests to cover all new fields and validation logic. Create comprehensive E2E test to validate the complete user experience with the extended form.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Database Models and Schemas
- Read `app/server/db/models.py` to understand current `UserExperience` model structure
- Extend the `UserExperience` model or create new `UserProfile` model with columns for:
  - `name` (String, 100 chars, required)
  - `employment_status` (String, 50 chars, required)
  - `employment_status_other` (String, 50 chars, nullable)
  - `industry` (String, 100 chars, nullable)
  - `role` (String, 100 chars, nullable)
  - `primary_use_context` (String, 50 chars, required)
  - `tried_ai_before` (Boolean, required)
  - `ai_tools_used` (JSON array, nullable)
  - `usage_frequency` (String, 50 chars, required)
  - `comfort_level` (Integer, 1-5, required)
  - `goals` (JSON array, required, max 3 items)
  - `challenges` (JSON array, nullable)
  - `learning_preference` (String, 50 chars, required)
  - `additional_comments` (Text, 500 chars, nullable)
- Update `app/server/models/schemas.py` to add all new fields to `UserCreate` Pydantic model with proper validation (character limits, email format, required fields)
- Add validation for goals array (must have exactly 3 items)
- Create database migration if using Alembic, or document schema change for manual migration

### 2. Update Backend Services and Routes
- Update `app/server/services/user_service.py` `create_user` function to:
  - Accept and process all new fields from `UserCreate` schema
  - Create/update the extended user profile record
  - Maintain backward compatibility with magic link generation
- Verify `app/server/api/routes/auth.py` `/register` endpoint handles expanded payload correctly
- No changes needed to magic link flow, authentication, or session management

### 3. Write Backend Tests
- Create `app/server/tests/test_registration_extended.py` with comprehensive test coverage:
  - Test successful registration with all required fields
  - Test successful registration with all fields (required + optional)
  - Test validation failures for missing required fields
  - Test character limit enforcement (name, email, employment_status_other, industry, role, ai_tools_other, additional_comments)
  - Test email format validation
  - Test goals array validation (must select exactly 3)
  - Test comfort_level range validation (1-5)
  - Test conditional field logic (employment_status_other only valid if employment_status is "Other")
  - Test JSON array fields properly store and retrieve (ai_tools_used, goals, challenges)
  - Test duplicate email rejection (existing user test should still pass)
- Run tests: `cd app/server && uv run pytest tests/test_registration_extended.py -v`

### 4. Update Frontend Types
- Update `app/client/src/lib/api/types.ts` `UserCreate` interface to match new backend schema:
  - Add all new required fields
  - Add all new optional fields with proper TypeScript types
  - Use string arrays for multi-select fields (ai_tools_used, goals, challenges)
  - Ensure types match Pydantic schema exactly

### 5. Rebuild Registration Form Component
- Update `app/client/src/pages/Register.tsx`:
  - Expand `formData` state to include all new fields with proper initial values
  - Create multi-section layout with headings:
    - "Basic Info" section
    - "Primary Use Context" section
    - "Current AI Experience" section
    - "Usage & Comfort Level" section
    - "Goals & Applications" section
    - "Biggest Challenge" section
    - "Learning Preference" section
    - "Additional Comments" (optional)
  - Implement all form controls:
    - Name input (text, 100 char limit, required)
    - Email input (email validation, 150 char limit, required) - existing field
    - Employment Status dropdown (required) with "Other" option that shows conditional text input
    - Industry input (text, 100 char limit, optional)
    - Role input (text, 100 char limit, optional)
    - Primary Use Context radio buttons (required)
    - "Tried AI before" Yes/No radio buttons (required)
    - AI Tools multi-select checkboxes (conditional, only shows if tried AI before = Yes)
    - Usage Frequency dropdown (required)
    - Comfort Level radio buttons 1-5 (required)
    - Goals multi-select checkboxes with counter and 3-item limit (required, must select exactly 3)
    - Challenges multi-select checkboxes (optional, unlimited)
    - Learning Preference radio buttons (required)
    - Additional Comments textarea (optional, 500 char limit)
  - Implement conditional rendering for:
    - Employment status "Other" text field (only show if employment_status === "Other")
    - AI tools question (only show if tried_ai_before === true)
    - AI tools "Other" text field (only show if "Other" checkbox is checked)
    - Goals "Other" text field (only show if "Other" checkbox is checked)
    - Challenges "Other" text field (only show if "Other" checkbox is checked)
  - Add character limit enforcement and display (e.g., "45/100 characters")
  - Add goals counter display (e.g., "2/3 selected") and disable additional selections when 3 are chosen
  - Implement client-side validation before submission
  - Maintain existing error handling, loading states, and navigation flow
  - Ensure accessible form labels and ARIA attributes
  - Apply consistent styling using existing Tailwind classes

### 6. Update Frontend Tests
- Update `app/client/src/pages/Register.test.tsx`:
  - Update existing tests to provide all new required fields
  - Add new test groups:
    - "Basic Info Section" - test name input, employment status dropdown, conditional "Other" field, industry, role
    - "Primary Use Context Section" - test radio button selection
    - "AI Experience Section" - test tried AI before toggle, conditional AI tools question, multi-select checkboxes
    - "Usage & Comfort Level Section" - test frequency dropdown, comfort level 1-5 selection
    - "Goals Section" - test multi-select with 3-item limit, counter display, disable logic when limit reached
    - "Challenges Section" - test multi-select checkboxes with unlimited selections
    - "Learning Preference Section" - test radio button selection
    - "Additional Comments" - test textarea with 500 char limit
    - "Character Limits" - test all character limits are enforced
    - "Conditional Logic" - test employment "Other" field, AI tools conditional, "Other" text fields for multi-selects
    - "Form Validation" - test required field validation, goals exactly 3 validation
    - "Form Submission" - test successful submission with all required fields, test with all fields including optional
  - Update mocked API response to expect expanded payload
  - Ensure all tests pass: `cd app/client && bun test Register.test.tsx`

### 7. Create E2E Test Specification
- Create `.claude/commands/e2e/test_extended_registration_form.md` following the pattern of `test_registration_flow.md`:
  - User Story: prospective user completing extended registration
  - Test Steps:
    1. Navigate to /register and take screenshot
    2. Verify all form sections and fields are present
    3. Fill in Basic Info section (name, email, employment status, industry, role)
    4. Take screenshot of filled Basic Info
    5. Select Primary Use Context (one radio button)
    6. Select "Yes" for tried AI before, verify AI tools checkboxes appear, select 2-3 tools
    7. Take screenshot showing conditional AI tools section
    8. Select Usage Frequency and Comfort Level
    9. Select exactly 3 goals, verify counter shows "3/3", verify cannot select 4th goal
    10. Take screenshot of Goals section with 3 selected
    11. Select 2-3 challenges (no limit)
    12. Select Learning Preference
    13. Enter optional additional comments
    14. Take screenshot of completed form
    15. Submit form
    16. Verify navigation to /thank-you
    17. Take screenshot of thank you page
    18. Use dev login to verify user was created with all submitted data
  - Success Criteria:
    - All form sections render correctly
    - Conditional logic works (employment "Other", AI tools question)
    - Goals limit enforces exactly 3 selections
    - Character limits prevent over-length input
    - Form submits successfully with valid data
    - User record contains all submitted information
    - At least 8 screenshots captured

### 8. Run E2E Test Validation
- Read `.claude/commands/test_e2e.md` to understand E2E test runner
- Execute the new E2E test: `/test_e2e .claude/commands/e2e/test_extended_registration_form.md` (this will be done during validation, documented here for implementer awareness)

### 9. Run All Validation Commands
- Execute all commands from the "Validation Commands" section below to ensure:
  - Zero backend test failures
  - Zero frontend test failures
  - Zero TypeScript errors
  - Successful frontend build
  - E2E test passes with all screenshots captured
- Fix any failures before marking feature complete

## Testing Strategy

### Unit Tests

**Backend Tests** (`app/server/tests/test_registration_extended.py`):
- Test Pydantic validation for all new fields
- Test character limit enforcement
- Test email format validation
- Test goals array validation (exactly 3 items required)
- Test comfort level range validation (1-5)
- Test JSON array serialization/deserialization
- Test user creation with all fields
- Test user creation with only required fields
- Test duplicate email rejection still works

**Frontend Tests** (`app/client/src/pages/Register.test.tsx`):
- Test all form sections render
- Test all input types (text, email, dropdown, radio, checkbox, textarea)
- Test character limit enforcement and display
- Test conditional rendering (employment "Other", AI tools, multi-select "Other" fields)
- Test multi-select goals with 3-item limit enforcement
- Test multi-select challenges with unlimited selections
- Test form submission with required fields only
- Test form submission with all fields
- Test client-side validation errors
- Test loading and error states
- Test navigation flow (register → thank you)

**E2E Tests** (`.claude/commands/e2e/test_extended_registration_form.md`):
- Test complete registration flow with new extended form
- Test conditional logic behavior in browser
- Test multi-select interactions
- Test character limit enforcement in real UI
- Test form submission and user creation
- Test visual rendering and layout
- Capture screenshots at each major step

### Edge Cases
- **Empty form submission**: Verify all required fields show validation errors
- **Partial form submission**: Verify specific missing required fields are identified
- **Character limit edge cases**: Test at limit, over limit, special characters
- **Email edge cases**: Invalid formats, extremely long emails, special characters
- **Goals selection edge cases**:
  - Try to select 0 goals → should show validation error
  - Try to select 1-2 goals → should show validation error
  - Try to select exactly 3 goals → should succeed
  - Try to select 4+ goals → UI should prevent (disable remaining checkboxes)
- **Multi-select "Other" edge cases**: Check/uncheck "Other" shows/hides text field
- **Employment "Other" edge case**: Change from "Other" to different option should clear "Other" text
- **AI tools conditional edge case**: Change "tried AI before" from Yes to No should clear AI tools selections
- **Comfort level edge cases**: Verify only 1-5 accepted, not 0 or 6+
- **Very long text in optional fields**: Test 500+ chars in additional comments
- **Special characters in text fields**: Test unicode, emojis, quotes, HTML tags
- **Rapid form changes**: Test changing selections quickly doesn't break state
- **Browser back button**: Test navigation back to form preserves entered data (current behavior)

## Acceptance Criteria
1. ✅ Registration form displays all sections: Basic Info, Primary Use Context, Current AI Experience, Usage & Comfort Level, Goals & Applications, Biggest Challenge, Learning Preference, Additional Comments
2. ✅ All required fields are enforced: name, email, employment status, primary use context, tried AI before, usage frequency, comfort level, goals (exactly 3), learning preference
3. ✅ All optional fields work correctly: industry, role, AI tools (conditional), challenges, additional comments
4. ✅ Character limits are enforced for all text inputs per specification (100, 150, 50, 500)
5. ✅ Email validation accepts valid emails and rejects invalid formats
6. ✅ Employment status "Other" option shows conditional text input limited to 50 chars
7. ✅ "Tried AI before" Yes option shows AI tools multi-select checkboxes
8. ✅ "Tried AI before" No option hides AI tools checkboxes
9. ✅ AI tools "Other" checkbox shows conditional text input limited to 100 chars
10. ✅ Goals section enforces exactly 3 selections (cannot submit with fewer or more)
11. ✅ Goals section displays selection counter (e.g., "2/3 selected")
12. ✅ Goals section disables remaining checkboxes when 3 are selected
13. ✅ Goals "Other" checkbox shows conditional text input limited to 100 chars
14. ✅ Challenges section allows unlimited selections (no limit enforcement)
15. ✅ Challenges "Other" checkbox shows conditional text input limited to 150 chars
16. ✅ Comfort level accepts only values 1-5
17. ✅ Additional comments textarea enforces 500 character limit
18. ✅ Form submits successfully with all required fields filled
19. ✅ Form submits successfully with all fields (required + optional) filled
20. ✅ Form shows appropriate validation errors for missing required fields
21. ✅ Form shows appropriate validation errors for invalid data (bad email, wrong goals count, etc.)
22. ✅ Backend stores all submitted data correctly in database
23. ✅ Backend validates all fields match Pydantic schema requirements
24. ✅ Magic link generation and authentication flow still works after registration
25. ✅ User can complete full flow: register with extended form → receive magic link → login → access courses
26. ✅ All backend tests pass (`cd app/server && uv run pytest`)
27. ✅ All frontend tests pass (`cd app/client && bun test`)
28. ✅ TypeScript compilation succeeds with no errors (`cd app/client && bun tsc --noEmit`)
29. ✅ Frontend builds successfully (`cd app/client && bun run build`)
30. ✅ E2E test passes and captures all required screenshots

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md` to understand the E2E test runner
- Read and execute `.claude/commands/e2e/test_extended_registration_form.md` to validate the extended registration form works end-to-end with all new fields, conditional logic, multi-select behavior, and character limits
- `cd app/server && uv run pytest` - Run all server tests to validate extended registration with zero regressions
- `cd app/server && uv run pytest tests/test_registration_extended.py -v` - Run new extended registration tests specifically
- `cd app/client && bun test Register.test.tsx` - Run updated frontend registration tests
- `cd app/client && bun tsc --noEmit` - Run TypeScript type checking to ensure no type errors
- `cd app/client && bun run build` - Run frontend build to validate the feature compiles correctly

## Notes

### Implementation Considerations
- **Form Length**: The extended form is significantly longer than the current simple form. Consider progressive disclosure or multi-step wizard if user testing shows the single-page approach is overwhelming. For MVP, implement as single scrollable page with clear section headings.
- **Data Storage**: Consider whether to store extended profile data in the existing `UserExperience` table (simpler, fewer joins) or create separate `UserProfile` table (better separation of concerns, more flexible). Recommendation: extend `UserExperience` to avoid over-engineering for MVP.
- **Goals Limit Logic**: The 3-item limit for goals requires careful UX: show counter, disable additional checkboxes when limit reached, and allow deselecting to select different goals. Ensure this is intuitive and well-tested.
- **Conditional Fields State**: When user changes "tried AI before" from Yes to No, decide whether to clear AI tools selections or preserve them. Recommendation: preserve selections in case of accidental toggle, only clear on form submission if "No" is final value.
- **Character Counters**: Display character counters for all limited text inputs to improve UX (e.g., "45/100 characters"). Update in real-time as user types.
- **Accessibility**: Ensure all radio buttons, checkboxes, and dropdowns have proper ARIA labels and keyboard navigation. Test with screen reader.
- **Mobile Responsiveness**: Test form on mobile viewport - consider stacking form controls vertically on small screens.
- **Validation Timing**: Decide between real-time validation (as user types) vs. on-blur vs. on-submit. Recommendation: on-blur for individual fields, comprehensive check on submit.

### Future Enhancements (Out of Scope for MVP)
- Multi-step wizard with progress indicator (Step 1 of 4, etc.)
- Save progress and return later functionality (requires backend session/draft storage)
- Pre-populate form for returning users who want to update their profile
- Analytics dashboard showing aggregate registration data (employment distribution, popular goals, common challenges)
- Use registration data for course recommendations on /courses page
- Email confirmation with summary of submitted registration data
- A/B testing different question wordings or form layouts
- Conditional routing based on experience level (beginner vs. advanced users see different courses first)

### Testing Notes
- Mock API calls in frontend tests will need to include all new fields in the request payload
- Backend tests should verify JSON arrays (ai_tools_used, goals, challenges) serialize/deserialize correctly
- E2E test should verify visual rendering of all form sections, not just data submission
- Consider snapshot testing for form layout to catch unintended UI regressions

### Database Migration
- If using Alembic for migrations, create migration script to add new columns to `user_experiences` table
- Existing users in database will have NULL values for new fields (acceptable since they registered before this feature)
- Consider adding a `registration_version` field to distinguish old simple registrations from new extended registrations for future analytics
