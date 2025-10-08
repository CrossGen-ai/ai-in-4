# E2E Test: Stripe Checkout Flow (Dashboard → Payment → Access Grant)

Test the complete Stripe payment integration from course discovery through checkout to access validation.

## User Story

As a registered user
I want to purchase a locked course using Stripe checkout
So that I can access premium course content after successful payment

## Prerequisites

- User is logged in
- Backend server running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Stripe webhook endpoint configured
- Test Stripe account configured with test mode enabled
- At least one paid course with active price exists in the database

## Test Setup

### Environment Variables Required
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Test Data Preparation
- Create test user: `stripe-test-${timestamp}@example.com`
- Ensure at least one product exists with:
  - Category: "alacarte" or "curriculum"
  - Active price (e.g., $49.99)
  - Product ID and Price ID available

## Test Steps

### 1. Authentication & Dashboard Access
1. Navigate to `/login`
2. Authenticate test user (via dev mode or magic link)
3. **Verify** redirect to `/dashboard`
4. Take screenshot: `01-dashboard-initial.png`
5. **Verify** dashboard heading: "Welcome Back"
6. **Verify** course cards are displayed

### 2. Locked Course Discovery
7. Scroll to "Full Curriculum" or "Individual Courses" section
8. Identify a locked (unpurchased) course card
9. Take screenshot: `02-locked-course-card.png`
10. **Verify** course card displays:
    - Course title
    - Course description
    - Price (formatted, e.g., "$49.99")
    - Category badge ("CURRICULUM" or "A-LA-CARTE")
    - Disabled "Locked" button
    - Paywall overlay visible
11. **Verify** "Unlock Access" button is visible in paywall overlay
12. **Verify** price is displayed in paywall overlay

### 3. Initiate Checkout
13. Click "Unlock Access" button on the paywall overlay
14. **Verify** button shows loading state: "Processing..."
15. **Verify** button is disabled during loading
16. Take screenshot: `03-checkout-loading.png`
17. Wait for Stripe checkout redirect
18. **Verify** URL changes to Stripe domain: `checkout.stripe.com`
19. Take screenshot: `04-stripe-checkout-page.png`
20. **Verify** Stripe checkout page displays:
    - Product name matches course
    - Price matches expected amount
    - Payment form is present

### 4. Complete Stripe Checkout (Test Mode)
21. Fill Stripe test payment form:
    - Email: Use test user email
    - Card Number: `4242 4242 4242 4242` (Stripe test card)
    - Expiry: Any future date (e.g., `12/34`)
    - CVC: Any 3 digits (e.g., `123`)
    - ZIP: Any 5 digits (e.g., `12345`)
22. Take screenshot: `05-stripe-form-filled.png`
23. Click "Pay" button
24. Wait for processing
25. Take screenshot: `06-stripe-processing.png`

### 5. Stripe Webhook Processing
26. **Verify** redirect back to application domain
27. **Expected URL**: `/dashboard` or `/payment/success` (depending on implementation)
28. Take screenshot: `07-post-payment-redirect.png`
29. Wait for webhook processing (may require 1-3 seconds)
30. **Note**: Webhook endpoint receives `payment_intent.succeeded` event

### 6. Verify Entitlement Grant
31. If not already on dashboard, navigate to `/dashboard`
32. Refresh page to ensure latest entitlement data loaded
33. Take screenshot: `08-dashboard-after-purchase.png`
34. Locate the previously locked course card
35. **Verify** course card state changed:
    - "Locked" button replaced with "Access Now" button
    - "Access Now" button is enabled (not disabled)
    - Paywall overlay is no longer visible
    - Button has green styling (`bg-green-600`)
36. Take screenshot: `09-unlocked-course-card.png`

### 7. Access Course Content
37. Click "Access Now" button on purchased course
38. **Verify** navigation to course detail page
39. **Expected URL**: `/course/{course_id}`
40. Take screenshot: `10-course-detail-page.png`
41. **Verify** course content is accessible:
    - Course title displayed
    - Course materials/content visible
    - No paywall or access denial

### 8. Verify Entitlement Persistence
42. Navigate back to `/dashboard`
43. Locate the purchased course again
44. **Verify** "Access Now" button still shows (entitlement persists)
45. Logout (if logout implemented)
46. Login again as same user
47. Navigate to `/dashboard`
48. **Verify** purchased course still shows "Access Now" (entitlement tied to user)

### 9. API Verification (Optional)
49. Make API call to `/api/payments/entitlements`
50. **Verify** response includes purchased course:
    ```json
    [
      {
        "price_id": "price_...",
        "product_id": "prod_...",
        "product_name": "Course Name",
        "status": "active",
        "granted_at": "2025-10-07T..."
      }
    ]
    ```

## Edge Cases to Test

### Edge Case 1: Checkout Session Expiration
**Test**: Initiate checkout but abandon before payment
- Click "Unlock Access"
- Wait for Stripe checkout page to load
- Close browser tab without paying
- Navigate back to `/dashboard`
- **Verify** course remains locked
- **Verify** no entitlement granted

### Edge Case 2: Duplicate Webhook Events (Idempotency)
**Test**: Simulate duplicate webhook delivery
- Complete a successful purchase
- Manually trigger webhook again with same `payment_intent.id`
- **Verify** only one entitlement exists in database
- **Verify** user is not charged twice
- **Verify** no duplicate referral credits (if applicable)

### Edge Case 3: User Navigation During Checkout
**Test**: User navigates away during Stripe checkout
- Click "Unlock Access"
- Wait for Stripe page load
- Use browser back button to return to dashboard
- **Verify** course still locked
- Return to Stripe and complete payment
- **Verify** entitlement granted correctly after completion

### Edge Case 4: Invalid Price ID
**Test**: Attempt checkout with non-existent price
- Modify frontend to use fake price_id: "price_invalid_123"
- Click "Unlock Access"
- **Verify** error handling:
  - User-friendly error message displayed
  - No redirect to Stripe
  - User can retry with valid product

### Edge Case 5: Network Failure During Checkout Initiation
**Test**: Simulate network error when creating checkout session
- Disconnect network before clicking "Unlock Access"
- Click button
- **Verify** error handling:
  - Loading state stops
  - Error message displayed to user
  - Button becomes clickable again for retry

## Success Criteria

✅ User can discover locked courses with visible pricing
✅ "Unlock Access" button initiates Stripe checkout correctly
✅ Stripe checkout URL contains `checkout.stripe.com`
✅ Stripe displays correct product and price
✅ Test payment completes successfully
✅ Webhook processes `payment_intent.succeeded` event
✅ Entitlement is granted to user in database
✅ Course card updates from "Locked" to "Access Now"
✅ User can access course content after purchase
✅ Entitlement persists across sessions
✅ Idempotency prevents duplicate charges/entitlements
✅ Error handling works for edge cases
✅ At least 10 screenshots captured at key steps

## Automated Test Implementation Notes

This test can be implemented as a Playwright E2E test with the following approach:

### Stripe Test Mode Considerations
- Use Stripe test API keys (not live keys)
- Stripe test cards: `4242 4242 4242 4242` (success), `4000 0000 0000 0002` (decline)
- Test mode webhooks can be triggered via Stripe CLI: `stripe listen --forward-to localhost:8000/api/payments/webhook`

### Webhook Simulation Options
**Option A: Stripe CLI (Recommended)**
```bash
# Terminal 1: Listen for webhooks
stripe listen --forward-to localhost:8000/api/payments/webhook

# Terminal 2: Run E2E test
npx playwright test test_stripe_checkout.spec.ts
```

**Option B: Mock Webhook Endpoint**
- Intercept Stripe checkout redirect
- Manually trigger webhook endpoint with mock payload
- Continue test flow

**Option C: Stripe Test Mode with Real Webhooks**
- Configure Stripe dashboard to forward test webhooks to ngrok/localtunnel URL
- Run test with real Stripe integration end-to-end

### Database Cleanup
- Before each test: Delete test user and their entitlements
- After test: Clean up test payment intents and entitlements
- Use database transactions or test database reset

## Related Backend Tests

This E2E test complements existing backend integration tests:
- `app/server/tests/test_payment_integration.py::test_full_checkout_to_entitlement_workflow`
- `app/server/tests/test_payment_integration.py::test_webhook_idempotency_prevents_duplicate_entitlements`

## Notes

- **Browser Context**: Test should run in authenticated browser context
- **Timing**: Allow 2-5 seconds after webhook for entitlement to be granted and UI to update
- **Stripe Test Mode**: All payments use Stripe test mode - no real money
- **Webhook Signing**: Test environment should disable webhook signature verification or use test webhook secret
- **Screenshots**: Capture screenshots at each major step for debugging failures
- **Retry Logic**: Implement retries for webhook-dependent assertions (eventual consistency)

## Manual Test Execution

For manual testing without automation:
1. Login to app with test account
2. Navigate to dashboard
3. Find locked course
4. Click "Unlock Access"
5. Complete Stripe test payment with `4242 4242 4242 4242`
6. Wait for redirect
7. Verify course now shows "Access Now"
8. Click to access course content

## Troubleshooting

**Issue**: Course remains locked after payment
**Check**:
- Webhook endpoint is reachable
- Webhook signature validation passes
- Database transaction committed successfully
- Frontend refetches entitlements after redirect

**Issue**: Stripe checkout doesn't load
**Check**:
- Stripe API keys configured correctly
- Price ID exists in Stripe account
- Checkout session creation succeeds (check network tab)
- CORS configured for Stripe domains

**Issue**: Duplicate entitlements created
**Check**:
- Idempotency logic in webhook handler
- Unique constraint on entitlements table
- Payment intent ID stored and checked before creating entitlement
