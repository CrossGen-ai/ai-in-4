# Chore: Fix Landing Page Redirect After Login

## Metadata
issue_number: `9`
adw_id: `9af7bb52`
issue_json: `{"number":9,"title":"fix landing page","body":"/chore make sure that after logging in the user gets directed to their course landing page not the main page"}`

## Chore Description
After successful authentication (both via magic link validation and dev login), users should be redirected to their course landing page (`/courses`) instead of the main landing page (`/`). Currently, the `DevLogin.tsx` component redirects authenticated users to `/` (line 38), which is inconsistent with the `Login.tsx` component that correctly redirects to `/courses` (line 29).

## Relevant Files
Use these files to resolve the chore:

- **app/client/src/pages/DevLogin.tsx** - Contains the dev login flow that currently redirects to `/` after successful authentication (line 38). This needs to be changed to redirect to `/courses` to match the behavior of the regular login flow.

- **app/client/src/pages/Login.tsx** - Contains the regular login flow that correctly redirects to `/courses` after magic link validation (line 29). This is the reference implementation for correct post-login behavior.

- **app/client/src/context/AuthContext.tsx** - Provides the authentication context and state management. No changes needed but useful for understanding the authentication flow.

- **app/client/src/pages/CourseLanding.tsx** - The protected course landing page where users should arrive after login. No changes needed but validates the target destination.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update DevLogin Redirect Target
- Open `app/client/src/pages/DevLogin.tsx`
- Locate line 38 where `navigate('/')` is called after successful dev login
- Change the redirect from `navigate('/')` to `navigate('/courses')` to match the behavior in `Login.tsx:29`
- This ensures consistent post-login behavior across both authentication flows

### 2. Run Validation Commands
- Execute the validation commands below to ensure the chore is complete with zero regressions
- Verify all tests pass
- Confirm type checking succeeds

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the chore is complete with zero regressions
- `cd app/client && yarn type-check` - Run TypeScript type checking to ensure no type errors were introduced
- `cd app/client && yarn test` - Run client tests to validate the chore is complete with zero regressions

## Notes
- This is a simple one-line change that ensures consistency between the dev login and regular login flows
- The change aligns the DevLogin behavior with the Login component's redirect pattern
- Both authentication methods should provide the same user experience post-login
- The `/courses` route is already protected by `ProtectedRoute` component, so only authenticated users can access it
- No backend changes are required as this is purely a frontend routing change
