# E2E Test: Registration and Magic Link Authentication Flow

Test the complete user registration and authentication flow for the AI Course Platform.

## User Story

As a prospective AI student
I want to register for AI learning sessions using a magic link authentication system
So that I can securely access course materials without managing passwords

## Test Steps

### 1. Landing Page
1. Navigate to the Application URL (`http://localhost:5173`)
2. Take a screenshot of the landing page
3. **Verify** the page displays "AI in 4" heading
4. **Verify** "Humanizing the Machine" tagline is visible
5. **Verify** "Get Started" button is present
6. Click "Get Started" button

### 2. Registration Page
7. **Verify** URL changes to `/register`
8. Take a screenshot of the registration page
9. **Verify** registration form sections are present:
   - Email input field
   - Name input field
   - Employment Information section
   - Primary Use Context section
   - AI Experience section
   - Goals & Applications section
   - Challenges section
   - Learning Preference section
   - Additional Comments textarea
   - Create Account button

10. Fill in the registration form:
    - Email: `test-user-${timestamp}@example.com` (use current timestamp to ensure uniqueness)
    - Name: "Test User"
    - Employment Status: Select "Employed full-time"
    - Industry: "Technology"
    - Role: "Software Engineer"
    - Primary Use Context: Select "Work/Professional tasks"
    - Tried AI Before: Select "Yes"
    - AI Tools Used: Check "ChatGPT"
    - Usage Frequency: Select "Daily"
    - Comfort Level: Select level 3 (middle of scale)
    - Goals: Check "Coding/technical tasks"
    - Challenges: Check "Writing effective prompts"
    - Learning Preference: Select "Hands-on practice with examples"
    - Additional Comments: "Looking forward to learning more about AI"

11. Take a screenshot of the filled form
12. Click "Create Account" button

### 3. Thank You Page
13. **Verify** URL changes to `/thank-you`
14. Take a screenshot of the thank you page
15. **Verify** page displays message about checking email
16. **Verify** explanation of magic link is shown
17. **Verify** "Go to Login" button is present

### 4. Dev Quick Login (Development Mode)
18. Navigate to `/dev-login`
19. Take a screenshot of dev login page
20. **Verify** list of users is displayed
21. **Verify** the test user created in step 10 appears in the list
22. Note: In development, magic link will be logged to server console

### 5. Login with Magic Link Simulation
23. Navigate to `/login`
24. Take a screenshot of login page
25. **Verify** email input field is present
26. **Verify** "Send Magic Link" button is present
27. **Verify** "Quick Login (Dev)" button is visible in development mode

### 6. Course Landing Page Access
28. Navigate directly to `/courses` (should redirect to login if not authenticated)
29. **Verify** either redirected to `/login` OR already authenticated
30. If redirected, check server logs for magic link token and use it:
    - Get the magic link token from server console logs
    - Navigate to `/login?token={token}`
    - Should automatically validate and redirect to courses
31. Take a screenshot of the course landing page
32. **Verify** welcome message is displayed
33. **Verify** user email is shown in header
34. **Verify** logout button is present
35. **Verify** available courses are listed
36. **Verify** course cards display:
    - Title
    - Description
    - Schedule
    - "Access Materials" button

### 7. User Profile Display
37. Scroll to "Your Profile" section
38. Take a screenshot of profile section
39. **Verify** user email is displayed
40. **Verify** "Member since" date is shown
41. **Verify** "Last login" timestamp is displayed

### 8. Logout Flow
42. Click "Logout" button
43. **Verify** redirected to landing page (`/`)
44. Take a screenshot after logout
45. Navigate to `/courses` again
46. **Verify** redirected to `/login` (protected route working)
47. Take final screenshot

## Success Criteria

- Landing page displays correctly with branding
- Registration form accepts all required and optional fields
- User creation succeeds and magic link is generated
- Thank you page explains magic link process
- Dev login shows registered users
- Magic link validation works (via dev mode or console log)
- Course landing page displays after successful authentication
- User profile information is shown correctly
- Courses are displayed with all details
- Logout clears authentication
- Protected routes redirect unauthenticated users
- At least 10 screenshots are captured at key steps
- All responsive design elements work on default viewport

## Notes

- In development mode, magic links are logged to server console instead of being emailed
- The test user email should use a timestamp to ensure uniqueness across test runs
- Server logs should be monitored to retrieve magic link tokens for authentication
- This test validates the complete registration → authentication → course access flow
