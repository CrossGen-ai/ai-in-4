# E2E Tests - Setup and Execution Guide

## Overview
End-to-end tests for the AI-in-4 course platform using Playwright. Tests validate user workflows including course access, payments, and entitlements.

## Prerequisites

### 1. Install Playwright (First Time Setup)
```bash
# From project root
npm install
npx playwright install chromium
```

### 2. Environment Setup
- **Frontend server**: `http://localhost:5173` (auto-started by Playwright)
- **Backend server**: `http://localhost:8000` (auto-started by Playwright)

## Running Tests

### Run All E2E Tests
```bash
npm run test:e2e
```

### Run Tests in UI Mode (Recommended for Development)
```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

### Debug Mode (Step Through Tests)
```bash
npm run test:e2e:debug
```

### Run Specific Test File
```bash
npx playwright test test_course_access.spec.ts
```

### Run Specific Test by Name
```bash
npx playwright test -g "free course immediate access"
```

## Test Files

| Test File | Description |
|-----------|-------------|
| `test_course_access.spec.ts` | Course access validation (free vs paid) |
| `test_stripe_checkout.spec.ts` | Stripe payment flow and entitlement creation |
| `test_extended_registration_form.spec.ts` | User registration extended form |

## Test Documentation

Each test has a corresponding `.md` file with detailed specifications:
- `test_course_access.md` - Comprehensive test scenarios and edge cases
- `test_stripe_checkout.md` - Payment integration test plan
- etc.

**Note**: The `.md` files are **documentation only**. The actual executable tests are the `.spec.ts` files.

## Common Issues

### Error: "Failed to spawn: pytest"
**Cause**: Trying to run `.md` documentation files instead of `.spec.ts` test files.
**Fix**: Use `npm run test:e2e` or `npx playwright test` commands.

### Error: "No tests found"
**Cause**: Playwright not installed or configuration missing.
**Fix**:
```bash
npm install
npx playwright install chromium
```

### Error: "Connection refused" (ECONNREFUSED)
**Cause**: Frontend or backend server not running.
**Fix**: Playwright auto-starts servers. If manual start needed:
```bash
# Terminal 1
cd app/client && npm run dev

# Terminal 2
cd app/server && uvicorn main:app --reload
```

### Error: "Browser not found"
**Cause**: Chromium browser not installed.
**Fix**:
```bash
npx playwright install chromium
```

## Test Results

- **HTML Report**: `playwright-report/index.html`
- **Screenshots**: `test-results/` (on failure)
- **Videos**: `test-results/` (on failure)
- **Traces**: `test-results/` (on retry)

### View HTML Report
```bash
npx playwright show-report
```

## Known Limitations

### Missing `/course/:id` Route (BLOCKING)
**Impact**: Several tests cannot verify course detail page navigation.
**Status**: Route needs to be added to `App.tsx`
**Affected Tests**:
- Free course navigation test (line 34-37 commented out)
- Return to dashboard after course access

**Required Fix**:
```tsx
// In app/client/src/App.tsx
<Route
  path="/course/:id"
  element={
    <ProtectedRoute>
      <CourseDetail />
    </ProtectedRoute>
  }
/>
```

### Admin API Endpoints
**Impact**: Tests requiring entitlement management use workarounds
**Status**: Implement admin API for test setup
**Endpoints Needed**:
- `POST /api/admin/entitlements` - Grant entitlement
- `PATCH /api/admin/entitlements/{id}` - Revoke/update entitlement

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npx playwright install chromium
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Writing New Tests

1. **Create spec file**: `.claude/commands/e2e/test_new_feature.spec.ts`
2. **Create documentation**: `.claude/commands/e2e/test_new_feature.md`
3. **Use existing patterns**: See `test_course_access.spec.ts` for examples
4. **Helper functions**: Reuse `authenticateUser()` and other helpers

### Test Template
```typescript
import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8000';

test.describe('Feature Name E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Setup code
  });

  test('test scenario name', async ({ page }) => {
    // Test implementation
  });
});
```

## Database Seeding

Tests assume the following data exists:
- Free course: `category='free'`
- Paid curriculum course: `category='curriculum'` with price
- Paid a-la-carte course: `category='alacarte'` with price
- Test users created via dev-login

## Performance Benchmarks

- Dashboard load: < 2 seconds
- Entitlement fetch: < 500ms
- Access check API: < 200ms
- Course navigation: < 1 second

## Support

For issues or questions:
1. Check existing test documentation (`.md` files)
2. Review Playwright docs: https://playwright.dev
3. Check test results and traces for debugging

## Last Updated
2025-10-07
