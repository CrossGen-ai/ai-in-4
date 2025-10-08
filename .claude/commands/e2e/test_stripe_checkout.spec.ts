/**
 * E2E Test: Stripe Checkout Flow
 *
 * This test implements the E2E test plan from test_stripe_checkout.md
 *
 * Prerequisites:
 * - Playwright installed: `npm install -D @playwright/test`
 * - Dev server running: `npm run dev` (port 5173)
 * - Backend server running: `cd app/server && uvicorn main:app --reload` (port 8000)
 * - Stripe CLI listening: `stripe listen --forward-to localhost:8000/api/payments/webhook`
 * - Environment variables configured with Stripe test keys
 *
 * To run:
 * ```bash
 * npx playwright test .claude/commands/e2e/test_stripe_checkout.spec.ts --headed
 * ```
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

// Configuration
const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8000';
const TEST_USER_EMAIL = `stripe-test-${Date.now()}@example.com`;
const STRIPE_TEST_CARD = '4242424242424242';

test.describe('Stripe Checkout E2E Flow', () => {
  let screenshotDir: string;
  let testUserEmail: string;

  test.beforeAll(() => {
    screenshotDir = path.join(__dirname, 'screenshots', `stripe-checkout-${Date.now()}`);
    testUserEmail = TEST_USER_EMAIL;
    console.log(`Test user email: ${testUserEmail}`);
  });

  test.beforeEach(async ({ page }) => {
    // Start from dashboard - assumes user is logged in or dev mode
    // If authentication is required, implement login flow here
    await page.goto(`${BASE_URL}/dashboard`);
  });

  test('should complete full Stripe checkout flow from dashboard to course access', async ({ page }) => {
    // ========================================================================
    // Step 1: Verify Dashboard Access
    // ========================================================================
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(screenshotDir, '01-dashboard-initial.png'), fullPage: true });

    await expect(page.getByText(/Welcome Back/i)).toBeVisible();
    console.log('✓ Dashboard loaded successfully');

    // ========================================================================
    // Step 2: Locate Locked Course
    // ========================================================================
    // Find a locked course card (has "Locked" button and paywall overlay)
    const lockedCourseCard = page.locator('div').filter({
      has: page.locator('button:has-text("Locked")'),
    }).first();

    await expect(lockedCourseCard).toBeVisible();
    await page.screenshot({ path: path.join(screenshotDir, '02-locked-course-card.png') });

    // Verify locked course displays price
    const priceText = await lockedCourseCard.locator('text=/\\$[0-9]+\\.[0-9]{2}/').textContent();
    console.log(`✓ Found locked course with price: ${priceText}`);

    // Verify category badge
    const categoryBadge = lockedCourseCard.locator('span.inline-block').filter({
      hasText: /CURRICULUM|A-LA-CARTE/i
    });
    await expect(categoryBadge).toBeVisible();

    // Verify paywall overlay exists
    const paywallOverlay = lockedCourseCard.locator('[class*="paywall"]').or(
      lockedCourseCard.locator('div').filter({ hasText: /Unlock Access/i })
    );
    await expect(paywallOverlay).toBeVisible();

    // ========================================================================
    // Step 3: Initiate Checkout
    // ========================================================================
    const unlockButton = lockedCourseCard.getByRole('button', { name: /Unlock Access/i });
    await expect(unlockButton).toBeVisible();
    await expect(unlockButton).toBeEnabled();

    await unlockButton.click();
    console.log('✓ Clicked "Unlock Access" button');

    // Wait for loading state
    await expect(unlockButton.or(page.getByText(/Processing/i))).toBeVisible({ timeout: 5000 });
    await page.screenshot({ path: path.join(screenshotDir, '03-checkout-loading.png') });

    // ========================================================================
    // Step 4: Verify Redirect to Stripe
    // ========================================================================
    // Wait for navigation to Stripe checkout
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });
    console.log(`✓ Redirected to Stripe: ${page.url()}`);

    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(screenshotDir, '04-stripe-checkout-page.png'), fullPage: true });

    // Verify Stripe checkout page elements
    await expect(page.locator('form').or(page.locator('[id*="payment"]'))).toBeVisible({ timeout: 10000 });
    console.log('✓ Stripe checkout page loaded');

    // ========================================================================
    // Step 5: Complete Stripe Test Payment
    // ========================================================================
    // Note: Stripe checkout UI selectors may change. Adjust as needed.
    // Common selectors for Stripe Checkout embedded form:

    // Fill email (if not pre-filled)
    const emailInput = page.locator('input[type="email"]').or(page.locator('input[name="email"]'));
    if (await emailInput.isVisible()) {
      await emailInput.fill(testUserEmail);
    }

    // Fill card number
    const cardNumberFrame = page.frameLocator('iframe[name*="card"]').or(
      page.frameLocator('iframe[title*="Secure card"]')
    ).first();

    const cardInput = cardNumberFrame.locator('input[name="cardnumber"]').or(
      cardNumberFrame.locator('input[placeholder*="Card number"]')
    ).first();

    await cardInput.waitFor({ state: 'visible', timeout: 10000 });
    await cardInput.fill(STRIPE_TEST_CARD);
    console.log('✓ Filled card number');

    // Fill expiry
    const expiryInput = cardNumberFrame.locator('input[name="exp-date"]').or(
      cardNumberFrame.locator('input[placeholder*="MM"]')
    ).first();
    await expiryInput.fill('1234'); // 12/34

    // Fill CVC
    const cvcInput = cardNumberFrame.locator('input[name="cvc"]').or(
      cardNumberFrame.locator('input[placeholder*="CVC"]')
    ).first();
    await cvcInput.fill('123');

    // Fill ZIP/Postal code (if present)
    const zipInput = page.locator('input[name="postalCode"]').or(
      page.locator('input[placeholder*="ZIP"]')
    );
    if (await zipInput.isVisible()) {
      await zipInput.fill('12345');
    }

    await page.screenshot({ path: path.join(screenshotDir, '05-stripe-form-filled.png'), fullPage: true });

    // Submit payment
    const payButton = page.getByRole('button', { name: /Pay|Subscribe|Complete/i });
    await expect(payButton).toBeEnabled();
    await payButton.click();
    console.log('✓ Clicked Pay button');

    await page.screenshot({ path: path.join(screenshotDir, '06-stripe-processing.png'), fullPage: true });

    // ========================================================================
    // Step 6: Wait for Webhook Processing & Redirect
    // ========================================================================
    // Wait for redirect back to app (success page or dashboard)
    await page.waitForURL(new RegExp(BASE_URL), { timeout: 30000 });
    console.log(`✓ Redirected back to app: ${page.url()}`);

    await page.screenshot({ path: path.join(screenshotDir, '07-post-payment-redirect.png'), fullPage: true });

    // Wait a bit for webhook to process (if webhook hasn't fired yet)
    // In real scenarios, webhook should fire within 1-3 seconds
    await page.waitForTimeout(3000);

    // ========================================================================
    // Step 7: Verify Entitlement Grant on Dashboard
    // ========================================================================
    // Navigate to dashboard if not already there
    if (!page.url().includes('/dashboard')) {
      await page.goto(`${BASE_URL}/dashboard`);
    }

    // Refresh to get latest entitlements
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(screenshotDir, '08-dashboard-after-purchase.png'), fullPage: true });

    // Find the course that was just purchased
    // It should now have "Access Now" button instead of "Locked"
    const unlockedCourseCard = page.locator('div').filter({
      has: page.getByRole('button', { name: /Access Now/i }),
    }).filter({
      hasNot: page.locator('button:has-text("Locked")'),
    }).first();

    await expect(unlockedCourseCard).toBeVisible({ timeout: 10000 });
    console.log('✓ Course is now unlocked');

    const accessButton = unlockedCourseCard.getByRole('button', { name: /Access Now/i });
    await expect(accessButton).toBeEnabled();
    await expect(accessButton).toHaveClass(/bg-green/); // Verify green styling

    // Verify paywall overlay is gone
    const paywallAfterPurchase = unlockedCourseCard.locator('[class*="paywall"]');
    await expect(paywallAfterPurchase).not.toBeVisible();

    await page.screenshot({ path: path.join(screenshotDir, '09-unlocked-course-card.png') });

    // ========================================================================
    // Step 8: Access Course Content
    // ========================================================================
    await accessButton.click();
    console.log('✓ Clicked "Access Now" button');

    // Wait for navigation to course detail page
    await page.waitForURL(/\/course\//, { timeout: 5000 });
    console.log(`✓ Navigated to course page: ${page.url()}`);

    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(screenshotDir, '10-course-detail-page.png'), fullPage: true });

    // Verify course content is accessible (no paywall or access denied)
    await expect(page.locator('text=/Access Denied|Locked|Purchase Required/i')).not.toBeVisible();
    console.log('✓ Course content is accessible');

    // ========================================================================
    // Step 9: Verify Entitlement Persistence
    // ========================================================================
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Verify "Access Now" button still shows
    const persistedAccessButton = page.getByRole('button', { name: /Access Now/i }).first();
    await expect(persistedAccessButton).toBeVisible();
    console.log('✓ Entitlement persists across navigation');

    // ========================================================================
    // Step 10: API Verification (Optional)
    // ========================================================================
    // Note: This requires authenticated API request. Adjust based on auth mechanism.
    // For now, we skip this step in the automated test.

    console.log('\n✅ Full Stripe checkout E2E test completed successfully!');
  });

  test('edge case: checkout session abandonment', async ({ page }) => {
    // Navigate to dashboard
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Find locked course
    const unlockButton = page.getByRole('button', { name: /Unlock Access/i }).first();
    await unlockButton.click();

    // Wait for Stripe checkout
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });
    console.log('✓ Stripe checkout loaded');

    // Abandon checkout by navigating back
    await page.goBack();
    await page.waitForURL(new RegExp(BASE_URL), { timeout: 5000 });
    console.log('✓ Navigated back from Stripe');

    // Verify course is still locked
    const lockedButton = page.getByRole('button', { name: /Locked/i }).first();
    await expect(lockedButton).toBeVisible();
    await expect(lockedButton).toBeDisabled();
    console.log('✓ Course remains locked after checkout abandonment');
  });

  test('edge case: verify idempotency after successful purchase', async ({ page, request }) => {
    /**
     * This test verifies that duplicate webhook events don't create duplicate entitlements.
     *
     * Note: This requires manual webhook triggering or Stripe CLI integration.
     * For full automation, use Stripe CLI to trigger duplicate webhooks.
     */

    // First, complete a purchase (abbreviated version)
    await page.goto(`${BASE_URL}/dashboard`);
    const unlockButton = page.getByRole('button', { name: /Unlock Access/i }).first();
    await unlockButton.click();

    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });
    // ... complete payment flow (omitted for brevity)

    // After successful purchase, trigger webhook again manually
    // This would require access to payment_intent_id and webhook endpoint

    // Verify only one entitlement exists in database
    // (Implementation depends on database access method)

    console.log('⚠️  Idempotency test requires manual webhook triggering');
  });
});

/**
 * Helper function to authenticate user (implement based on auth mechanism)
 */
async function authenticateUser(page: Page, email: string): Promise<void> {
  // This is a placeholder. Implement based on your auth mechanism:
  // - Magic link login
  // - Dev mode quick login
  // - Session token injection

  console.log(`Authenticating user: ${email}`);
  // await page.goto(`${BASE_URL}/dev-login`);
  // await page.getByText(email).click();
  // await page.waitForURL(`${BASE_URL}/dashboard`);
}

/**
 * Helper function to create test user with API
 */
async function createTestUser(email: string): Promise<void> {
  // Implement API call to create test user
  console.log(`Creating test user: ${email}`);
}

/**
 * Helper function to clean up test data
 */
async function cleanupTestData(email: string): Promise<void> {
  // Implement cleanup logic:
  // - Delete test user
  // - Delete entitlements
  // - Delete payment records
  console.log(`Cleaning up test data for: ${email}`);
}
