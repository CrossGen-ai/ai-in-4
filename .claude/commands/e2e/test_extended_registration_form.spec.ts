/**
 * E2E Test: Extended Registration Form
 *
 * This test is an executable Playwright E2E test that implements the test plan
 * from test_extended_registration_form.md
 *
 * To run this test, you'll need:
 * 1. Playwright installed (`npm install -D @playwright/test`)
 * 2. The dev server running on http://localhost:5173
 * 3. Run: `npx playwright test test_extended_registration_form.spec.ts`
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

test.describe('Extended Registration Form E2E', () => {
  let screenshotDir: string;

  test.beforeAll(() => {
    // Create screenshots directory
    screenshotDir = path.join(__dirname, 'screenshots', `run-${Date.now()}`);
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to registration page
    await page.goto('http://localhost:5173/register');
  });

  test('should complete full extended registration flow', async ({ page }) => {
    // Step 1: Verify initial page load
    await page.screenshot({ path: path.join(screenshotDir, '01-register-page-initial.png') });
    await expect(page.getByText('Create Your Account')).toBeVisible();

    // Verify all section headings
    await expect(page.getByText('Basic Info')).toBeVisible();
    await expect(page.getByText('Primary Use Context')).toBeVisible();
    await expect(page.getByText('Current AI Experience')).toBeVisible();
    await expect(page.getByText('Usage & Comfort Level')).toBeVisible();
    await expect(page.getByText('Goals & Applications')).toBeVisible();
    await expect(page.getByText('Biggest Challenge')).toBeVisible();
    await expect(page.getByText('Learning Preference')).toBeVisible();
    await expect(page.getByText('Additional Comments')).toBeVisible();

    // Step 2: Fill Basic Info Section
    await page.getByPlaceholder('Your full name').fill('Test User');
    await page.getByPlaceholder('you@example.com').fill('test-extended@example.com');

    // Select Employment Status
    const employmentSelect = page.locator('select').first();
    await employmentSelect.selectOption('Employed full-time');

    await page.getByPlaceholder('e.g., Technology, Healthcare, Education').fill('Technology');
    await page.getByPlaceholder('e.g., Software Engineer, Teacher, Manager').fill('Software Engineer');

    await page.screenshot({ path: path.join(screenshotDir, '02-basic-info-filled.png') });

    // Verify character counters update
    await expect(page.getByText('9/100')).toBeVisible(); // "Test User" = 9 chars

    // Step 3: Select Primary Use Context
    await page.getByLabel('Work/Professional tasks').check();
    await page.screenshot({ path: path.join(screenshotDir, '03-primary-use-context.png') });

    // Step 4: Fill AI Experience Section
    await page.getByLabel('Yes', { exact: true }).check();

    // Wait for AI tools checkboxes to appear
    await expect(page.getByText('Which AI tools have you used?')).toBeVisible();

    // Select AI tools
    await page.getByLabel('ChatGPT').check();
    await page.getByLabel('Claude').check();
    await page.getByLabel('Perplexity').check();

    await page.screenshot({ path: path.join(screenshotDir, '04-ai-experience-filled.png') });

    // Step 5: Fill Usage & Comfort Level
    const frequencySelect = page.locator('select').nth(1);
    await frequencySelect.selectOption('Daily');

    await page.getByLabel(/3 - Somewhat comfortable/).check();
    await page.screenshot({ path: path.join(screenshotDir, '05-usage-comfort-level.png') });

    // Step 6: Fill Goals Section (Exactly 3)
    await page.getByLabel('Writing/content creation').check();
    await page.getByLabel('Research and information gathering').check();
    await page.getByLabel('Coding/technical tasks').check();

    // Verify counter shows 3/3
    await expect(page.getByText('3/3 selected')).toBeVisible();

    // Verify 4th checkbox is disabled
    const fourthGoalCheckbox = page.getByLabel('Data analysis');
    await expect(fourthGoalCheckbox).toBeDisabled();

    await page.screenshot({ path: path.join(screenshotDir, '06-goals-three-selected.png') });

    // Step 7: Select Challenges
    await page.getByLabel("Understanding what AI can/can't do").check();
    await page.getByLabel('Writing effective prompts').check();
    await page.getByLabel('Integrating AI into my workflow').check();

    await page.screenshot({ path: path.join(screenshotDir, '07-challenges-selected.png') });

    // Step 8: Select Learning Preference
    await page.getByLabel('Hands-on practice with examples').check();
    await page.screenshot({ path: path.join(screenshotDir, '08-learning-preference.png') });

    // Step 9: Fill Additional Comments
    const comment = "I'm excited to learn more about AI and how to integrate it into my daily workflow. Looking forward to practical examples!";
    await page.getByPlaceholder('Share any additional thoughts or questions...').fill(comment);

    // Verify character counter updates
    await expect(page.getByText(`${comment.length}/500`)).toBeVisible();
    await page.screenshot({ path: path.join(screenshotDir, '09-additional-comments.png') });

    // Step 10: Submit Form
    await page.screenshot({ path: path.join(screenshotDir, '10-complete-form-before-submit.png') });

    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for navigation to /thank-you
    await page.waitForURL('http://localhost:5173/thank-you', { timeout: 10000 });

    // Step 11: Verify Thank You Page
    expect(page.url()).toBe('http://localhost:5173/thank-you');
    await page.screenshot({ path: path.join(screenshotDir, '11-thank-you-page.png') });

    // Verify success message
    await expect(page.getByText(/thank you|success/i)).toBeVisible();

    // Step 12: Verify User Data via Dev Login
    await page.goto('http://localhost:5173/login');

    // Use dev login with the test email
    await page.getByPlaceholder(/email/i).fill('test-extended@example.com');

    // Click dev login button (assuming there's a dev login option)
    await page.getByRole('button', { name: /dev login|login/i }).click();

    // Wait for successful login (adjust based on actual redirect)
    await page.waitForURL(/courses|dashboard|home/, { timeout: 5000 });

    await page.screenshot({ path: path.join(screenshotDir, '12-dev-login-success.png') });
  });

  test('should enforce exactly 3 goals selection', async ({ page }) => {
    // Fill minimum required fields
    await page.getByPlaceholder('Your full name').fill('Test User');
    await page.getByPlaceholder('you@example.com').fill('test@example.com');
    await page.locator('select').first().selectOption('Student');
    await page.getByLabel('Educational purposes').check();
    await page.getByLabel('Yes', { exact: true }).check();
    await page.locator('select').nth(1).selectOption('Weekly');
    await page.getByLabel(/3 - Somewhat comfortable/).check();
    await page.getByLabel('Hands-on practice with examples').check();

    // Select only 2 goals
    await page.getByLabel('Writing/content creation').check();
    await page.getByLabel('Research and information gathering').check();

    // Try to submit
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Should show error
    await expect(page.getByText('Please select exactly 3 goals.')).toBeVisible();
  });

  test('should show/hide conditional fields correctly', async ({ page }) => {
    // Test employment status "Other" field
    const employmentSelect = page.locator('select').first();

    // Initially, "Other" field should not be visible
    await expect(page.getByPlaceholder('Your employment status')).not.toBeVisible();

    // Select "Other"
    await employmentSelect.selectOption('Other');
    await expect(page.getByPlaceholder('Your employment status')).toBeVisible();

    // Change back to "Student"
    await employmentSelect.selectOption('Student');
    await expect(page.getByPlaceholder('Your employment status')).not.toBeVisible();

    // Test AI tools conditional section
    await expect(page.getByText('Which AI tools have you used?')).not.toBeVisible();

    await page.getByLabel('Yes', { exact: true }).check();
    await expect(page.getByText('Which AI tools have you used?')).toBeVisible();

    await page.getByLabel('No', { exact: true }).check();
    await expect(page.getByText('Which AI tools have you used?')).not.toBeVisible();
  });

  test('should validate character limits', async ({ page }) => {
    // Test name character limit (100)
    const nameInput = page.getByPlaceholder('Your full name');
    await expect(nameInput).toHaveAttribute('maxlength', '100');

    // Test email character limit (150)
    const emailInput = page.getByPlaceholder('you@example.com');
    await expect(emailInput).toHaveAttribute('maxlength', '150');

    // Test additional comments limit (500)
    const commentsTextarea = page.getByPlaceholder('Share any additional thoughts or questions...');
    await expect(commentsTextarea).toHaveAttribute('maxlength', '500');
  });
});
