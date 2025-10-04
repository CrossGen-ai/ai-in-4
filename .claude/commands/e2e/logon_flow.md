# E2E Test: Magic Link Login

Test login functionality for returning users using the magic link authentication flow.

## User Story

As a registered user
I want to log in with a magic link sent to my email
So that I can securely access the course portal without remembering a password

## Test Steps

1. Navigate to the `Login Page URL` (ai-in-4.crossgen-ai.com/login).

2. Take a screenshot of the initial login page.

3. **Verify** UI elements are present:

   * Email input field
   * “Send Login Link” button

4. Enter a valid registered email: `testuser@example.com`.

5. Take a screenshot of the filled email input.

6. Click the “Send Login Link” button.

7. **Verify** confirmation message appears: “Check your email for a login link.”

8. Take a screenshot of the confirmation state.

9. In test environment, retrieve the magic link from Postmark (mock or test inbox).

10. Open the magic link in a browser.

11. **Verify** the user is logged in and redirected to the **Course Portal dashboard**.

12. Take a screenshot of the logged-in state.

13. **Verify** user session is persisted (refresh page → still logged in).

## Success Criteria

* Login page loads with correct UI elements.
* Valid email triggers a magic link email.
* Clicking the magic link logs the user in.
* User is redirected to the course portal after login.
* Session persists across page refresh.
* 3+ screenshots are taken.
