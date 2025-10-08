import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8000';

test.describe('Course Access Validation E2E', () => {
  let testUserEmail: string;

  test.beforeEach(async ({ page }) => {
    // Authenticate user via dev-login
    testUserEmail = `test-${Date.now()}@example.com`;
    await authenticateUser(page, testUserEmail);
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
  });

  test('free course immediate access', async ({ page }) => {
    // Find free course card
    const freeCourseCard = page.locator('div').filter({
      has: page.locator('span:has-text("FREE")')
    }).first();

    await expect(freeCourseCard).toBeVisible();

    // Verify no paywall overlay
    const paywall = freeCourseCard.locator('[class*="paywall"]');
    await expect(paywall).not.toBeVisible();

    // Verify "Access Now" button
    const accessButton = freeCourseCard.getByRole('button', { name: /Access Now/i });
    await expect(accessButton).toBeEnabled();
    await expect(accessButton).toHaveClass(/bg-green/);

    // Click and verify navigation (BLOCKED until /course/:id route exists)
    // await accessButton.click();
    // await page.waitForURL(/\/course\//);
    // await expect(page.locator('text=/Access Denied/i')).not.toBeVisible();
  });

  test('paid course locked without entitlement', async ({ page }) => {
    // Find locked paid course (has "Locked" button)
    const lockedCourseCard = page.locator('div').filter({
      has: page.locator('button:has-text("Locked")')
    }).first();

    await expect(lockedCourseCard).toBeVisible();

    // Verify price display
    const priceText = await lockedCourseCard.locator('text=/\\$[0-9]+/').textContent();
    expect(priceText).toBeTruthy();

    // Verify paywall overlay
    const paywall = lockedCourseCard.locator('[class*="paywall"]').or(
      lockedCourseCard.locator('div').filter({ hasText: /Unlock Access/i })
    );
    await expect(paywall).toBeVisible();

    // Verify "Locked" button is disabled
    const lockedButton = lockedCourseCard.getByRole('button', { name: /Locked/i });
    await expect(lockedButton).toBeDisabled();
    await expect(lockedButton).toHaveClass(/cursor-not-allowed/);
  });

  test('direct URL navigation without authentication', async ({ page, context }) => {
    // Clear auth state
    await context.clearCookies();

    // Attempt to access dashboard
    await page.goto(`${BASE_URL}/dashboard`);

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('entitlement grant unlocks course', async ({ page, request }) => {
    // Find a locked course and capture its price_id
    const lockedCourseCard = page.locator('div').filter({
      has: page.locator('button:has-text("Locked")')
    }).first();

    await expect(lockedCourseCard).toBeVisible();

    // Extract price_id from the card (implementation depends on data attributes)
    // For this test, we'll manually create an entitlement via API

    const testPriceId = 'price_test_123'; // Replace with actual price_id extraction

    // Grant entitlement via API (requires admin endpoint or DB access)
    await request.post(`${API_URL}/api/admin/entitlements`, {
      data: {
        user_email: testUserEmail,
        price_id: testPriceId,
        status: 'active'
      }
    });

    // Refresh dashboard
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify course is now unlocked
    const unlockedCard = page.locator('div').filter({
      has: page.getByRole('button', { name: /Access Now/i })
    }).first();

    await expect(unlockedCard).toBeVisible();

    const accessButton = unlockedCard.getByRole('button', { name: /Access Now/i });
    await expect(accessButton).toBeEnabled();

    // Verify paywall is gone
    const paywall = unlockedCard.locator('[class*="paywall"]');
    await expect(paywall).not.toBeVisible();
  });

  test('entitlement persistence across navigation', async ({ page }) => {
    // Assume user has at least one entitlement (from previous test or setup)

    // Verify "Access Now" button exists
    const accessButton = page.getByRole('button', { name: /Access Now/i }).first();
    await expect(accessButton).toBeVisible();

    // Navigate away
    await page.goto(`${BASE_URL}/courses`);

    // Navigate back
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Verify entitlement still exists
    await expect(accessButton).toBeVisible();
  });

  test('return to dashboard after accessing free course', async ({ page }) => {
    // Find and click free course
    const freeCourseCard = page.locator('div').filter({
      has: page.locator('span:has-text("FREE")')
    }).first();

    const accessButton = freeCourseCard.getByRole('button', { name: /Access Now/i });

    // Note: This test is currently blocked by missing /course/:id route
    // await accessButton.click();
    // await page.waitForURL(/\/course\//);

    // For now, test navigation simulation
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Verify dashboard reloads correctly
    await expect(page.locator('h1:has-text("Welcome Back")')).toBeVisible();

    // Verify course cards render
    const courseCards = page.locator('div[class*="grid"] > div').filter({
      has: page.locator('button:has-text("Access Now"), button:has-text("Locked")')
    });
    await expect(courseCards.first()).toBeVisible();

    // Check for no unnecessary API calls (monitor network tab)
    const apiCalls: string[] = [];
    page.on('request', req => {
      if (req.url().includes('/api/')) {
        apiCalls.push(req.url());
      }
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Should only call entitlements API once per reload
    const entitlementCalls = apiCalls.filter(url => url.includes('/entitlements'));
    expect(entitlementCalls.length).toBeLessThanOrEqual(1);
  });

  test('direct navigation to paid course without entitlement', async ({ page }) => {
    // Get a paid course ID
    const lockedCourseCard = page.locator('div').filter({
      has: page.locator('button:has-text("Locked")')
    }).first();

    // Extract course ID (assuming data-testid or similar attribute)
    // For demo, using hardcoded test course ID
    const paidCourseId = 'prod_paid_course_001';

    // Attempt direct navigation
    await page.goto(`${BASE_URL}/course/${paidCourseId}`);

    // Should redirect to dashboard or show access denied
    // Current implementation: catch-all redirects to /
    await page.waitForURL(/\/(dashboard)?$/);

    // OR if route exists and shows paywall:
    // const paywall = page.locator('[data-testid="paywall-overlay"]');
    // await expect(paywall).toBeVisible();
    // const courseContent = page.locator('[data-testid="course-content"]');
    // await expect(courseContent).not.toBeVisible();
  });

  test('edge case: user without any entitlements', async ({ page, context }) => {
    // Create brand new user
    const newUserEmail = `newuser-${Date.now()}@example.com`;

    // Clear existing session
    await context.clearCookies();

    // Authenticate as new user
    await authenticateUser(page, newUserEmail);
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Verify dashboard loads
    await expect(page.locator('h1:has-text("Welcome Back")')).toBeVisible();

    // Verify free courses accessible
    const freeCourseButton = page.getByRole('button', { name: /Access Now/i }).first();
    await expect(freeCourseButton).toBeVisible();

    // Verify paid courses locked
    const lockedButton = page.getByRole('button', { name: /Locked/i }).first();
    await expect(lockedButton).toBeVisible();
    await expect(lockedButton).toBeDisabled();

    // Check for console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.waitForTimeout(2000);
    expect(consoleErrors).toHaveLength(0);
  });

  test('edge case: missing or invalid stripe price IDs', async ({ page }) => {
    // This test requires seeding a product with null price_id
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Find products without prices
    const productsResponse = await page.request.get(`${API_URL}/api/courses/products`);
    const products = await productsResponse.json();

    const productWithoutPrice = products.find((p: any) => !p.price_id);

    if (productWithoutPrice) {
      // Verify card renders without crashing
      const card = page.locator(`[data-course-id="${productWithoutPrice.id}"]`);

      // Card should exist but show disabled state
      await expect(card).toBeVisible();

      // No purchase button should be rendered
      const purchaseButton = card.locator('button:has-text("Purchase")');
      await expect(purchaseButton).not.toBeVisible();

      // Should show "Coming Soon" or similar
      const comingSoon = card.locator('text=/Coming Soon|Not Available/i');
      await expect(comingSoon).toBeVisible();
    }
  });

  test('edge case: revoked entitlement during session', async ({ page, request }) => {
    // Grant entitlement
    const testPriceId = 'price_test_revoke';
    const entitlementResponse = await request.post(`${API_URL}/api/admin/entitlements`, {
      data: {
        user_email: testUserEmail,
        price_id: testPriceId,
        payment_intent_id: `pi_revoke_${Date.now()}`,
        status: 'active'
      }
    });

    const entitlement = await entitlementResponse.json();

    // Verify access granted
    await page.reload();
    await page.waitForLoadState('networkidle');

    const accessButton = page.getByRole('button', { name: /Access Now/i }).first();
    await expect(accessButton).toBeVisible();

    // Revoke entitlement (simulate refund)
    await request.patch(`${API_URL}/api/admin/entitlements/${entitlement.id}`, {
      data: { status: 'refunded' }
    });

    // Refresh page to fetch updated entitlements
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify course is now locked
    const lockedButton = page.getByRole('button', { name: /Locked/i }).first();
    await expect(lockedButton).toBeVisible();

    // Access button should be gone
    await expect(accessButton).not.toBeVisible();

    // If on course page, paywall should appear
    // (Requires /course/:id route implementation)
  });
});

/**
 * Helper: Authenticate user via dev-login or standard flow
 */
async function authenticateUser(page: Page, email: string): Promise<void> {
  await page.goto(`${BASE_URL}/dev-login`);

  // Dev-login flow (adjust based on actual implementation)
  const emailInput = page.locator('input[type="email"]');
  if (await emailInput.isVisible()) {
    await emailInput.fill(email);
    await page.getByRole('button', { name: /Login/i }).click();
  } else {
    // Click existing user if dev-login shows user list
    const userButton = page.getByText(email);
    if (await userButton.isVisible()) {
      await userButton.click();
    }
  }

  await page.waitForURL(`${BASE_URL}/dashboard`);
}
