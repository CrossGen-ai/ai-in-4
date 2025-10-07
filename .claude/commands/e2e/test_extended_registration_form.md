# E2E Test: Extended Registration Form

## User Story
As a prospective AI learning platform user, I want to complete the extended registration form with comprehensive information about my background, AI experience, and learning goals, so that the platform can personalize my learning experience.

## Test Steps

### 1. Navigate to Registration Page
- Navigate to http://localhost:5173/register
- Take screenshot: `01-register-page-initial.png`
- Verify page title: "Create Your Account"
- Verify all section headings are present:
  - Basic Info
  - Primary Use Context
  - Current AI Experience
  - Usage & Comfort Level
  - Goals & Applications
  - Biggest Challenge
  - Learning Preference
  - Additional Comments

### 2. Fill Basic Info Section
- Fill in Name: "Test User"
- Fill in Email: "test-extended@example.com"
- Select Employment Status: "Employed full-time"
- Fill in Industry: "Technology"
- Fill in Role: "Software Engineer"
- Take screenshot: `02-basic-info-filled.png`
- Verify character counters update correctly

### 3. Select Primary Use Context
- Select radio button: "Work/Professional tasks"
- Take screenshot: `03-primary-use-context.png`

### 4. Fill AI Experience Section
- Select "Yes" for "Have you tried AI tools before?"
- Wait for AI tools checkboxes to appear
- Select checkboxes:
  - ChatGPT
  - Claude
  - Perplexity
- Take screenshot: `04-ai-experience-filled.png`
- Verify conditional AI tools section is visible

### 5. Fill Usage & Comfort Level
- Select Usage Frequency: "Daily"
- Select Comfort Level: "3 - Somewhat comfortable"
- Take screenshot: `05-usage-comfort-level.png`

### 6. Fill Goals Section (Exactly 3)
- Select goal checkboxes:
  - "Writing/content creation"
  - "Research and information gathering"
  - "Coding/technical tasks"
- Verify counter shows "3/3 selected"
- Verify 4th checkbox becomes disabled
- Take screenshot: `06-goals-three-selected.png`

### 7. Select Challenges
- Select challenge checkboxes:
  - "Understanding what AI can/can't do"
  - "Writing effective prompts"
  - "Integrating AI into my workflow"
- Take screenshot: `07-challenges-selected.png`

### 8. Select Learning Preference
- Select radio button: "Hands-on practice with examples"
- Take screenshot: `08-learning-preference.png`

### 9. Fill Additional Comments (Optional)
- Enter text: "I'm excited to learn more about AI and how to integrate it into my daily workflow. Looking forward to practical examples!"
- Verify character counter updates
- Take screenshot: `09-additional-comments.png`

### 10. Submit Form
- Take screenshot of complete form: `10-complete-form-before-submit.png`
- Click "Create Account" button
- Wait for navigation to /thank-you

### 11. Verify Thank You Page
- Verify URL is http://localhost:5173/thank-you
- Take screenshot: `11-thank-you-page.png`
- Verify success message appears

### 12. Verify User Data in Database (Dev Login)
- Navigate to http://localhost:5173/login
- Use dev login with email: "test-extended@example.com"
- Verify user can access the system
- Take screenshot: `12-dev-login-success.png`

## Success Criteria

All of the following must be true for the test to pass:

1. ✅ All form sections render correctly with proper headings
2. ✅ Character counters display and update correctly for all text inputs
3. ✅ Employment status dropdown includes all expected options
4. ✅ Conditional "Other" field appears when employment status "Other" is selected
5. ✅ AI tools checkboxes only appear when "tried AI before" is "Yes"
6. ✅ Goals section enforces exactly 3 selections (counter shows 3/3, additional checkboxes disabled)
7. ✅ Challenges section allows unlimited selections (no disable logic)
8. ✅ All required fields prevent submission if empty
9. ✅ Form submits successfully with valid data
10. ✅ User is redirected to /thank-you page after successful registration
11. ✅ User record is created in database with all submitted information
12. ✅ Dev login works with the newly created user
13. ✅ At least 10 screenshots are captured successfully

## Expected Data in Database

After registration, the database should contain a user record with:
- email: "test-extended@example.com"
- name: "Test User"
- employment_status: "Employed full-time"
- industry: "Technology"
- role: "Software Engineer"
- primary_use_context: "Work/Professional tasks"
- tried_ai_before: true
- ai_tools_used: ["ChatGPT", "Claude", "Perplexity"]
- usage_frequency: "Daily"
- comfort_level: 3
- goals: ["Writing/content creation", "Research and information gathering", "Coding/technical tasks"]
- challenges: ["Understanding what AI can/can't do", "Writing effective prompts", "Integrating AI into my workflow"]
- learning_preference: "Hands-on practice with examples"
- additional_comments: "I'm excited to learn more about AI..."

## Edge Cases to Test (Optional)

If time permits, test these edge cases:

1. Try to submit with only 2 goals selected (should show error)
2. Try to submit with 4 goals selected (should be prevented by UI)
3. Change employment status from "Other" back to "Student" (conditional field should disappear)
4. Change "tried AI before" from "Yes" to "No" (AI tools should disappear)
5. Test character limits by entering maximum characters in each field
6. Test form with minimum required fields only (no optional fields filled)
