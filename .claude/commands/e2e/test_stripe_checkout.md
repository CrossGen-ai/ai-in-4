# E2E Test: Stripe Checkout Flow (Dashboard → Payment → Access Grant)

Test the complete Stripe payment integration from course discovery through checkout to access validation.

## User Story

As a registered user
I want to purchase a locked course using Stripe checkout
So that I can access premium course content after successful payment

## Prerequisites

- User is logged in
- User has completed profile with `employment_status` set (required for pricing)
- Backend server running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Stripe webhook endpoint configured
- Test Stripe account configured with test mode enabled
- At least one paid course with employment-based pricing exists in the database

## Test Setup

### Environment Variables Required
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Test Data Preparation
- Create test user: `stripe-test-${timestamp}@example.com`
- Set user's employment status (required for price selection):
  - Student/Reduced Rate: "Student", "Between jobs", "Homemaker", "Retired", "Other"
  - Employed Rate: "Employed full-time", "Employed part-time", "Self-employed/Freelancer"
- Ensure at least one product exists with employment-based pricing:
  - Category: "alacarte" or "curriculum"
  - Two active prices per product:
    - Student/Reduced Rate (e.g., $9.00 for alacarte, $97.00 for curriculum)
    - Employed Rate (e.g., $97.00 for alacarte, $497.00 for curriculum)
  - Each price has `eligible_employment_statuses` metadata
  - Product ID and Price IDs available

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

### 4. Verify Employment-Based Price Selection
21. **Verify** Stripe checkout displays correct price based on employment status:
    - If user is "Student", "Between jobs", etc. → verify reduced rate (e.g., $9.00 for alacarte)
    - If user is "Employed full-time", "Employed part-time", etc. → verify employed rate (e.g., $97.00 for alacarte)
22. Take screenshot: `04a-price-verification.png`
23. **Verify** line item on Stripe checkout matches expected price tier

### 5. Complete Stripe Checkout (Test Mode)
24. Fill Stripe test payment form:
    - Email: Use test user email
    - Card Number: `4242 4242 4242 4242` (Stripe test card)
    - Expiry: Any future date (e.g., `12/34`)
    - CVC: Any 3 digits (e.g., `123`)
    - ZIP: Any 5 digits (e.g., `12345`)
25. Take screenshot: `05-stripe-form-filled.png`
26. Click "Pay" button
27. Wait for processing
28. Take screenshot: `06-stripe-processing.png`

### 6. Stripe Webhook Processing
29. **Verify** redirect back to application domain
30. **Expected URL**: `/dashboard` or `/payment/success` (depending on implementation)
31. Take screenshot: `07-post-payment-redirect.png`
32. Wait for webhook processing (may require 1-3 seconds)
33. **Note**: Webhook endpoint receives `payment_intent.succeeded` event

### 7. Verify Entitlement Grant
34. If not already on dashboard, navigate to `/dashboard`
35. Refresh page to ensure latest entitlement data loaded
36. Take screenshot: `08-dashboard-after-purchase.png`
37. Locate the previously locked course card
38. **Verify** course card state changed:
    - "Locked" button replaced with "Access Now" button
    - "Access Now" button is enabled (not disabled)
    - Paywall overlay is no longer visible
    - Button has green styling (`bg-green-600`)
39. Take screenshot: `09-unlocked-course-card.png`

### 8. Access Course Content
40. Click "Access Now" button on purchased course
41. **Verify** navigation to course detail page
42. **Expected URL**: `/course/{course_id}`
43. Take screenshot: `10-course-detail-page.png`
44. **Verify** course content is accessible:
    - Course title displayed
    - Course materials/content visible
    - No paywall or access denial

### 9. Verify Entitlement Persistence
45. Navigate back to `/dashboard`
46. Locate the purchased course again
47. **Verify** "Access Now" button still shows (entitlement persists)
48. Logout (if logout implemented)
49. Login again as same user
50. Navigate to `/dashboard`
51. **Verify** purchased course still shows "Access Now" (entitlement tied to user)

### 10. API Verification (Optional)
52. Make API call to `/api/payments/entitlements`
53. **Verify** response includes purchased course:
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

### 11. Referral Flow Testing (Complete Flow)

**Prerequisites**:
- Referrer user: `referrer-${timestamp}@example.com`
- Referee user: `referee-${timestamp}@example.com`

#### 11.1 Setup Referrer User

54. Create and login as referrer user
55. Navigate to `/dashboard`
56. Locate referral code section
57. **Verify** referral code displayed (format: 6-8 uppercase alphanumeric)
58. Take screenshot: `11-referrer-code.png`
59. Copy referral code (e.g., `ALICE123`)
60. **Verify** initial stats show:
    - Total Referrals: 0
    - Pending Referrals: 0
    - Total Credits: $0.00

#### 11.2 Complete Referral Purchase

61. Logout from referrer account
62. Create NEW test user: `referee-${timestamp}@example.com`
63. Complete registration and set employment status (e.g., "Student")
64. Navigate to `/dashboard`
65. Locate locked course (e.g., "Prompt Engineering - $9.00")
66. Click "Unlock Access" button
67. **On checkout page**, look for referral code input field
68. Enter referrer code: `ALICE123`
69. Take screenshot: `12-checkout-with-referral.png`
70. Complete payment with test card `4242 4242 4242 4242`
71. Wait for redirect to dashboard

#### 11.3 Verify Referee Access Granted

72. **Verify** purchased course now shows "Access Now"
73. **Verify** course content accessible
74. Take screenshot: `13-referee-course-unlocked.png`

#### 11.4 Verify Referrer Credit Applied

75. Logout from referee account
76. Login as original referrer user (`referrer-${timestamp}@example.com`)
77. Navigate to `/dashboard` or `/referrals` (if exists)
78. Take screenshot: `14-referrer-stats-updated.png`
79. **Verify** referral stats updated:
    - Total Referrals: 1
    - Pending Referrals: 0 (or 1 if credit pending)
    - Total Credits: $2.25 (25% of $9.00)
80. **Verify** referral history shows:
    - Referee email: `referee-${timestamp}@example.com`
    - Purchase amount: $9.00
    - Credit earned: $2.25
    - Status: "completed"

#### 11.5 API Verification

81. Make API call to `/api/payments/referrals`:
    ```json
    {
      "referral_code": "ALICE123",
      "total_referrals": 1,
      "pending_referrals": 0,
      "total_credits": 225  // in cents
    }
    ```
82. **Verify** response matches UI display

#### 11.6 Database Verification (Optional)

83. Query database for referral record:
    ```sql
    SELECT * FROM referrals
    WHERE referrer_id = (SELECT id FROM users WHERE email = 'referrer-...')
    ORDER BY created_at DESC LIMIT 1;
    ```
84. **Verify**:
    - `referee_email` matches referee user
    - `payment_intent_id` matches Stripe payment
    - `status` = "completed"
    - `credit_amount` = 225 (25% of 900 cents)

### Edge Case: Self-Referral Prevention

**Test**: User attempts to use their own referral code

85. Login as user
86. Note user's own referral code (e.g., `ALICE123`)
87. Navigate to locked course
88. Click "Unlock Access"
89. Enter own referral code: `ALICE123`
90. Attempt to proceed
91. **Verify** error message: "Cannot use your own referral code"
92. **Verify** checkout does NOT proceed
93. Take screenshot: `15-self-referral-error.png`

### Edge Case: Invalid Referral Code

**Test**: User enters non-existent referral code

94. Navigate to locked course
95. Click "Unlock Access"
96. Enter fake referral code: `INVALID999`
97. Attempt to proceed
98. **Verify** error message: "Invalid referral code"
99. **Verify** checkout does NOT proceed
100. Take screenshot: `16-invalid-referral-error.png`

### Edge Case: Referral Without Code (Optional)

**Test**: Purchase without referral code still works

101. Navigate to locked course
102. Click "Unlock Access"
103. Leave referral code field EMPTY
104. Complete payment normally
105. **Verify** purchase succeeds
106. **Verify** no referral record created
107. **Verify** course access granted

### Success Criteria - Referral Flow

✅ Referrer code displayed to user
✅ Referral code can be entered at checkout
✅ Payment succeeds with valid referral code
✅ 25% credit applied to referrer (correct calculation)
✅ Referral stats updated correctly (count + credits)
✅ Self-referral attempt blocked with clear error
✅ Invalid referral code rejected with clear error
✅ Optional referral code (checkout works without it)
✅ Database referral record created with correct data
✅ Referee receives course access as normal

## Edge Cases to Test

### Edge Case 1: Employment-Based Price Selection
**Test**: Verify correct price selected based on user's employment status
- Test Scenario A: Student user
  - Set user employment_status to "Student"
  - Initiate checkout for curriculum course
  - **Verify** Stripe displays $97.00 (student rate), not $497.00 (employed rate)
  - Complete payment
  - **Verify** correct price charged
- Test Scenario B: Employed user
  - Set user employment_status to "Employed full-time"
  - Initiate checkout for same curriculum course
  - **Verify** Stripe displays $497.00 (employed rate), not $97.00 (student rate)
  - Complete payment
  - **Verify** correct price charged

### Edge Case 2: Missing Employment Status
**Test**: Verify error handling when user lacks employment status
- Create user without employment_status set
- Attempt to initiate checkout
- **Verify** error response: "User employment status not found. Please complete your profile."
- **Verify** user is not redirected to Stripe
- **Verify** user sees helpful error message

### Edge Case 3: Checkout Session Expiration
**Test**: Initiate checkout but abandon before payment
- Click "Unlock Access"
- Wait for Stripe checkout page to load
- Close browser tab without paying
- Navigate back to `/dashboard`
- **Verify** course remains locked
- **Verify** no entitlement granted

### Edge Case 4: Duplicate Webhook Events (Idempotency)
**Test**: Simulate duplicate webhook delivery
- Complete a successful purchase
- Manually trigger webhook again with same `payment_intent.id`
- **Verify** only one entitlement exists in database
- **Verify** user is not charged twice
- **Verify** no duplicate referral credits (if applicable)

### Edge Case 5: User Navigation During Checkout
**Test**: User navigates away during Stripe checkout
- Click "Unlock Access"
- Wait for Stripe page load
- Use browser back button to return to dashboard
- **Verify** course still locked
- Return to Stripe and complete payment
- **Verify** entitlement granted correctly after completion

### Edge Case 6: Invalid Price ID
**Test**: Attempt checkout with non-existent price
- Modify frontend to use fake price_id: "price_invalid_123"
- Click "Unlock Access"
- **Verify** error handling:
  - User-friendly error message displayed
  - No redirect to Stripe
  - User can retry with valid product

### Edge Case 7: Network Failure During Checkout Initiation
**Test**: Simulate network error when creating checkout session
- Disconnect network before clicking "Unlock Access"
- Click button
- **Verify** error handling:
  - Loading state stops
  - Error message displayed to user
  - Button becomes clickable again for retry

### Edge Case 8: Attempting to Purchase Already-Owned Course

**Test**: Verify user can't double-purchase same course

**Scenario A: UI Prevention (Recommended)**

1. Complete purchase for "Prompt Engineering" course
2. Wait for entitlement to be granted
3. Verify course shows "Access Now" button
4. **Verify** "Unlock Course" button is HIDDEN or DISABLED
5. Take screenshot: `17-already-owned-button-hidden.png`
6. **Expected**: User cannot initiate checkout for owned course
7. **Benefit**: Prevents accidental double-purchase

**Scenario B: Backend Prevention (If UI doesn't prevent)**

1. Complete purchase for "Prompt Engineering" course
2. Manually trigger checkout API call:
   ```bash
   curl -X POST http://localhost:8000/api/payments/checkout \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"product_id": "prod_alacarte_prompt_eng"}'
   ```
3. **Expected Responses**:
   - **Option 1**: 400 Bad Request - "You already own this course"
   - **Option 2**: 200 OK - Returns existing entitlement (idempotent)
   - **Option 3**: 200 OK - Creates new checkout session (allows repurchase)
4. **Current Behavior**: [TO BE DETERMINED]

**Scenario C: User Intent to Gift/Transfer**

1. User owns course
2. User wants to purchase again as gift for friend
3. **Current System**: No gift/transfer functionality
4. **Future Enhancement**: Add "Purchase as Gift" flow

**Implementation Decision Needed**:
- [ ] Should UI hide checkout button for owned courses? (RECOMMENDED)
- [ ] Should backend reject duplicate purchases?
- [ ] Should backend allow repurchase (e.g., for gifting)?
- [ ] Should we track purchase history separate from entitlements?

**Test Steps**:

8. Login as user who completed purchase in main test flow
9. Navigate to `/dashboard`
10. Locate purchased course (shows "Access Now")
11. Inspect page source for "Unlock Course" button
12. **Verify** button does not exist in DOM OR is `disabled`
13. If button exists and is enabled:
    - Click button
    - **Verify** appropriate error handling (400 error or idempotent response)
14. Take screenshot: `18-already-owned-handling.png`

**Success Criteria**:
✅ UI prevents initiating checkout for owned courses (button hidden/disabled)
✅ OR backend gracefully handles duplicate purchase attempts
✅ No accidental double-charges occur
✅ User sees clear messaging if they try to repurchase

**Notes for Implementation**:
- Check `hasAccess` property in frontend CourseCard component
- If `hasAccess === true`, render "Access Now" instead of "Unlock Course"
- Backend could add check: "If user already has active entitlement, return 400"
- Consider future feature: "Purchase as Gift" with separate gift code system

## Success Criteria

✅ User has employment_status set in profile (prerequisite)
✅ User can discover locked courses with visible pricing
✅ Correct price selected based on user's employment status
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
