# Stripe Testing & Documentation Improvements - Implementation Plan

## 🎯 INSTRUCTIONS FOR EXECUTION

**This document is an executable implementation plan. Follow these instructions:**

1. **Use TodoWrite tool** at the start to create a todo list with all 13 items
2. **Mark each item as in_progress** before starting work
3. **Mark each item as completed** immediately after finishing (with evidence)
4. **Provide specific evidence** for each completion (file path, line numbers, test output)
5. **Run tests after each code change** to verify no regressions
6. **Do NOT skip items** - execute sequentially in order
7. **If blocked**, document the blocker and continue to next item

---

## 📋 MASTER CHECKLIST

- [ ] **Item 1** (HIGH): Add webhook idempotency test with database verification
- [ ] **Item 2** (HIGH): Add refunded entitlement access denial test
- [ ] **Item 3** (HIGH): Document webhook signature verification security risk
- [ ] **Item 4** (HIGH): Add database schema diagram to STRIPE_TESTING.md
- [ ] **Item 5** (HIGH): Add error code reference table to STRIPE_TESTING.md
- [ ] **Item 6** (MEDIUM): Add referral flow to E2E test markdown
- [ ] **Item 7** (MEDIUM): Add invalid employment status test
- [ ] **Item 8** (MEDIUM): Add manual product creation guide to STRIPE_TESTING.md
- [ ] **Item 9** (MEDIUM): Add production deployment checklist to STRIPE_TESTING.md
- [ ] **Item 10** (MEDIUM): Add test data cleanup section to STRIPE_TESTING.md
- [ ] **Item 11** (LOW): Add frontend unit test placeholder for CourseCard
- [ ] **Item 12** (LOW): Add already-purchased negative test case to E2E markdown
- [ ] **Item 13** (LOW): Add conditional_docs triggers for referrals/refunds

---

## 🔴 HIGH PRIORITY ITEMS (1-5)

### Item 1: Webhook Idempotency Test with Database Verification

**Issue**: Current test at `app/server/tests/test_payments.py:725-765` uses mocks, so it doesn't prove the database idempotency constraint actually works. We need a real database test that verifies only ONE entitlement exists after duplicate webhooks.

**Why Critical**: If idempotency fails in production, users could get charged multiple times or receive duplicate referral credits.

**File to Modify**: `/app/server/tests/test_payments.py`

**Implementation**:

Add this test after line 765 (after `test_webhook_idempotency_for_duplicate_events`):

```python
@pytest.mark.asyncio
async def test_webhook_idempotency_creates_single_entitlement_in_database(
    client, override_get_current_user, test_db
):
    """
    Test webhook idempotency with actual database verification.

    Verifies that sending the same payment_intent.succeeded event twice
    results in only ONE entitlement in the database (not two).

    This is the REAL idempotency test - previous test used mocks.
    """
    # Arrange - create product and price
    product = StripeProduct(
        id="prod_idempotent_test",
        name="Idempotency Test Product",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_idempotent_test",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student", "Employed full-time"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Webhook payload
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_idempotent_test_12345",  # Same ID for both calls
                "amount": 1000,
                "metadata": {
                    "user_id": str(override_get_current_user.id),
                    "price_id": "price_idempotent_test",
                    "user_email": override_get_current_user.email,
                }
            }
        }
    }

    # Act - send webhook TWICE with same payment_intent.id
    response1 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )

    response2 = client.post(
        "/api/payments/webhook",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"},
    )

    # Assert - both requests should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200

    # CRITICAL ASSERTION: Only ONE entitlement should exist in database
    result = await test_db.execute(
        select(Entitlement).where(
            Entitlement.stripe_payment_intent_id == "pi_idempotent_test_12345"
        )
    )
    entitlements = list(result.scalars().all())

    assert len(entitlements) == 1, (
        f"Expected exactly 1 entitlement, found {len(entitlements)}. "
        f"Idempotency failed - duplicate entitlement created!"
    )

    # Verify the single entitlement has correct data
    entitlement = entitlements[0]
    assert entitlement.user_id == override_get_current_user.id
    assert entitlement.stripe_price_id == "price_idempotent_test"
    assert entitlement.status == "active"
```

**Acceptance Criteria**:
- Test passes with exactly 1 entitlement after duplicate webhooks
- Test fails if you remove idempotency check in `grant_entitlement()` (validate test works)
- All other payment tests still pass

**Testing**:
```bash
cd /app/server
uv run pytest tests/test_payments.py::test_webhook_idempotency_creates_single_entitlement_in_database -v
uv run pytest tests/test_payments.py -v  # Verify no regressions
```

**Evidence Required**:
- File path and line numbers where test was added
- Terminal output showing test passed
- Confirmation all 21 payment tests pass

---

### Item 2: Refunded Entitlement Access Denial Test

**Issue**: Access control logic checks `status == "active"` but there's no test verifying that `status == "refunded"` correctly denies access. If a payment is refunded via Stripe, the entitlement status changes to "refunded", but we never test this path.

**Why Critical**: Users could retain course access after refunds, resulting in revenue loss.

**File to Modify**: `/app/server/tests/test_entitlement_service.py`

**Implementation**:

Add this test after line 713 (after the last `check_course_access` test):

```python
@pytest.mark.asyncio
async def test_check_course_access_denies_refunded_entitlement(
    test_db: AsyncSession,
    test_user: User,
    alacarte_course,
    test_stripe_price: StripePrice,
):
    """
    Test that refunded entitlements do NOT grant course access.

    Critical for ensuring users lose access after refunds.
    """
    # Arrange - grant entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_refund_test_123",
        db=test_db,
    )

    # Act - revoke entitlement (simulates refund)
    await revoke_entitlement(entitlement.id, test_db)

    # Verify entitlement status changed to "refunded"
    await test_db.refresh(entitlement)
    assert entitlement.status == "refunded"

    # Assert - access should be denied
    has_access = await check_course_access(test_user.id, alacarte_course, test_db)
    assert has_access is False, (
        "User should NOT have access after entitlement is refunded, "
        f"but check_course_access returned {has_access}"
    )


@pytest.mark.asyncio
async def test_check_course_access_curriculum_denies_refunded_entitlement(
    test_db: AsyncSession,
    test_user: User,
    curriculum_course,
    curriculum_price: StripePrice,
):
    """
    Test that refunded curriculum entitlements do NOT grant bundle access.

    Verifies category-based access control also respects refund status.
    """
    # Arrange - grant curriculum entitlement
    entitlement = await grant_entitlement(
        user_id=test_user.id,
        price_id=curriculum_price.id,
        payment_intent_id="pi_curriculum_refund_test",
        db=test_db,
    )

    # Verify access granted initially
    has_access_before = await check_course_access(test_user.id, curriculum_course, test_db)
    assert has_access_before is True

    # Act - revoke entitlement
    await revoke_entitlement(entitlement.id, test_db)

    # Assert - access should be denied after refund
    has_access_after = await check_course_access(test_user.id, curriculum_course, test_db)
    assert has_access_after is False, (
        "User should NOT have curriculum access after refund"
    )
```

**Acceptance Criteria**:
- Both tests pass
- Tests verify both alacarte and curriculum categories respect refunded status
- All existing entitlement tests still pass

**Testing**:
```bash
cd /app/server
uv run pytest tests/test_entitlement_service.py::test_check_course_access_denies_refunded_entitlement -v
uv run pytest tests/test_entitlement_service.py::test_check_course_access_curriculum_denies_refunded_entitlement -v
uv run pytest tests/test_entitlement_service.py -v  # Verify no regressions
```

**Evidence Required**:
- File path and line numbers where tests were added
- Terminal output showing both tests passed
- Confirmation all entitlement tests pass

---

### Item 3: Document Webhook Signature Verification Security Risk

**Issue**: Line 197-199 in `app/server/api/routes/payments.py` has webhook signature verification commented out:

```python
# TODO: Verify webhook signature
# if not stripe_service.verify_webhook_signature(body, stripe_signature):
#     raise HTTPException(status_code=400, detail="Invalid signature")
```

This is a **critical security vulnerability** for production deployment. Attackers could send fake webhook events to grant themselves free entitlements.

**Why Critical**: Production security risk. Fake webhooks could grant unauthorized course access.

**File to Modify**: `/app/docs/testing/STRIPE_TESTING.md`

**Implementation**:

Add this new section after line 489 (after "## Best Practices" section):

```markdown
## 🚨 CRITICAL SECURITY CONSIDERATIONS

### Webhook Signature Verification (PRODUCTION BLOCKER)

**Current Status**: ❌ **DISABLED** (Line 197 in `api/routes/payments.py`)

```python
# TODO: Verify webhook signature
# if not stripe_service.verify_webhook_signature(body, stripe_signature):
#     raise HTTPException(status_code=400, detail="Invalid signature")
```

**Risk**: Without signature verification, attackers can send fake webhook events to:
- Grant themselves free course access
- Create fake referral credits
- Manipulate entitlement status

**Impact**: Complete bypass of payment system. Revenue loss and unauthorized access.

**Priority**: 🔴 **MUST FIX BEFORE PRODUCTION DEPLOYMENT**

### Implementation Required

**Step 1: Create Stripe Service**

Create `/app/server/services/stripe_service.py`:

```python
"""Stripe webhook signature verification."""
import stripe
from core.config import settings

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Stripe webhook signature.

    Args:
        payload: Raw request body (bytes, not parsed JSON)
        signature: stripe-signature header value

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
        return True
    except stripe.SignatureVerificationError:
        return False
    except Exception:
        return False
```

**Step 2: Uncomment Verification in payments.py**

Update `api/routes/payments.py` line 197-199:

```python
# Import at top of file
from services import stripe_service

# In webhook handler (line 197-199)
if not stripe_service.verify_webhook_signature(body, stripe_signature):
    logger.warning(f"Webhook signature verification failed")
    raise HTTPException(status_code=400, detail="Invalid signature")
```

**Step 3: Add Test Coverage**

Add to `tests/test_payments.py`:

```python
def test_webhook_rejects_invalid_signature(client):
    """Test webhook rejects events with invalid signatures."""
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_test", "metadata": {}}}
    }

    # Mock signature verification to return False
    with patch("api.routes.payments.stripe_service.verify_webhook_signature") as mock_verify:
        mock_verify.return_value = False

        response = client.post(
            "/api/payments/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "invalid_signature"},
        )

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]
```

**Step 4: Configure Webhook Secret**

Obtain webhook signing secret:

**Local Development** (Stripe CLI):
```bash
stripe listen --forward-to http://localhost:8000/api/payments/webhook --print-secret
# Copy whsec_... to .env as STRIPE_WEBHOOK_SECRET
```

**Production** (Stripe Dashboard):
1. Go to Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/api/payments/webhook`
3. Select events: `payment_intent.succeeded`
4. Copy signing secret (whsec_...) to production secrets manager

### Testing Signature Verification

**Test Valid Signature**:
```bash
stripe trigger payment_intent.succeeded
# Should see: --> payment_intent.succeeded [200]
```

**Test Invalid Signature**:
```bash
curl -X POST http://localhost:8000/api/payments/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: invalid_sig" \
  -d '{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_test"}}}'
# Should return: 400 Bad Request - Invalid signature
```

### Before Production Checklist

- [ ] `stripe_service.verify_webhook_signature()` implemented
- [ ] Verification uncommented in `payments.py:197`
- [ ] Test coverage added for invalid signatures
- [ ] `STRIPE_WEBHOOK_SECRET` configured in production secrets
- [ ] Manual test passed with real Stripe webhooks
- [ ] Invalid signature test passed

**DO NOT deploy to production until all items checked.**
```

**Acceptance Criteria**:
- New "CRITICAL SECURITY CONSIDERATIONS" section added to STRIPE_TESTING.md
- Section appears before "Best Practices" section
- Includes code examples for implementation
- Includes testing instructions
- Includes production checklist

**Testing**:
- Read the file to verify section was added correctly
- Check markdown formatting renders properly

**Evidence Required**:
- File path: `/app/docs/testing/STRIPE_TESTING.md`
- Line numbers where section was added
- Confirmation section includes all required subsections (implementation, testing, checklist)

---

### Item 4: Add Database Schema Diagram to STRIPE_TESTING.md

**Issue**: Developers need to understand table relationships between courses, products, prices, and entitlements. Currently, this is implicit and requires reading code.

**Why Critical**: Understanding schema is essential for debugging payment flow issues and understanding access control logic.

**File to Modify**: `/app/docs/testing/STRIPE_TESTING.md`

**Implementation**:

Add this new section after line 39 (after "## Overview" section):

```markdown
## Database Schema Overview

Understanding the database relationships is critical for debugging payment and access control issues.

### Entity Relationship Diagram

```
┌─────────────────┐
│ users           │
│ - id (PK)       │
│ - email         │
└────────┬────────┘
         │
         │ 1:1
         │
┌────────▼────────────────┐
│ user_experience         │
│ - user_id (FK)          │
│ - employment_status ◄───┼─── Used for price selection
│ - name                  │
└─────────────────────────┘


┌─────────────────────────┐         ┌──────────────────────┐
│ courses                 │         │ stripe_products      │
│ - id (PK)               │         │ - id (PK) ◄──────────┼─── Stripe ID (prod_xxx)
│ - title                 │         │ - name               │
│ - category              │    ┌────┤ - category           │
│ - stripe_product_id ────┼────┘    │ - active             │
│   (FK, nullable)        │         └──────────┬───────────┘
└─────────────────────────┘                    │
                                               │ 1:N
  ┌────────────────────────────────────────────┘
  │
  │    ┌──────────────────────────────┐
  └────► stripe_prices                │
       │ - id (PK) ◄──────────────────┼─── Stripe ID (price_xxx)
       │ - product_id (FK)             │
       │ - amount                      │
       │ - currency                    │
       │ - stripe_metadata ◄───────────┼─── Contains eligible_employment_statuses
       │ - active                      │
       └──────────────┬────────────────┘
                      │
                      │ 1:N
                      │
       ┌──────────────▼─────────────────────┐
       │ entitlements                        │
       │ - id (PK)                           │
       │ - user_id (FK) ────┐                │
       │ - stripe_price_id (FK)              │
       │ - stripe_payment_intent_id (UNIQUE) │◄─── Idempotency key
       │ - status (active|refunded)          │
       │ - created_at                        │
       └─────────────────────────────────────┘
```

### Key Relationships

1. **User → UserExperience** (1:1)
   - `user_experience.employment_status` determines which price tier to use
   - Employment statuses: "Student", "Between jobs", "Employed full-time", etc.

2. **Course → StripeProduct** (N:1, nullable)
   - `courses.stripe_product_id` links course to Stripe product
   - **NULL for free courses** (no payment required)
   - **REQUIRED for alacarte/unique courses** (per-course access)
   - **Shared for curriculum courses** (bundle access)

3. **StripeProduct → StripePrice** (1:N)
   - One product has 2 prices: student rate + employed rate
   - `stripe_prices.stripe_metadata` contains `eligible_employment_statuses` array
   - Price selection: user's employment status matches array → select this price

4. **User → Entitlement ← StripePrice** (N:M via entitlements)
   - `entitlements` is the join table that grants access
   - `stripe_payment_intent_id` is **UNIQUE** (idempotency constraint)
   - Only `status="active"` grants access (`status="refunded"` denies access)

### Critical Fields Explained

| Table | Field | Purpose | Example Values |
|-------|-------|---------|----------------|
| `user_experience` | `employment_status` | Determines price tier | "Student", "Employed full-time" |
| `courses` | `stripe_product_id` | Links course to product | `prod_xxx` or NULL (free courses) |
| `courses` | `category` | Access control logic | "free", "alacarte", "curriculum", "unique" |
| `stripe_prices` | `stripe_metadata` | Eligibility criteria | `{"eligible_employment_statuses": ["Student", ...]}` |
| `stripe_prices` | `amount` | Price in cents | 9700 = $97.00 |
| `entitlements` | `stripe_payment_intent_id` | Idempotency key | `pi_xxx` (UNIQUE constraint) |
| `entitlements` | `status` | Access control | "active" (grants access), "refunded" (denies) |

### Access Control Flow

```
User wants to access course
         ↓
Check course.category
         ↓
    ┌────┴────┐
    │  free?  │ → YES → ✅ Grant Access (no entitlement check)
    └────┬────┘
         NO
         ↓
    ┌──────────────┐
    │ alacarte or  │ → YES → Check: user has entitlement to
    │   unique?    │         course.stripe_product_id?
    └──────┬───────┘            ↓
         NO                  ✅ YES → Grant Access
         ↓                   ❌ NO  → Deny Access
    ┌────────────┐
    │ curriculum?│ → YES → Check: user has entitlement to
    └────────────┘         ANY curriculum product?
                               ↓
                           ✅ YES → Grant Access (bundle)
                           ❌ NO  → Deny Access
```

### Common Schema-Related Bugs

| Bug | Cause | Fix |
|-----|-------|-----|
| Alacarte course grants access to all alacarte | `courses.stripe_product_id` is NULL | Set product_id for each course |
| User can't checkout | `user_experience.employment_status` is NULL | Require profile completion |
| Wrong price shown | Price metadata doesn't match employment status | Update `stripe_metadata` array |
| Course locked after payment | No entitlement created | Check webhook metadata flow |
| Refunded user retains access | Entitlement status still "active" | Verify `revoke_entitlement()` called |

### Querying the Schema

**Find user's entitlements**:
```sql
SELECT
    e.id,
    e.status,
    sp.amount,
    spr.name AS product_name,
    e.created_at
FROM entitlements e
JOIN stripe_prices sp ON e.stripe_price_id = sp.id
JOIN stripe_products spr ON sp.product_id = spr.id
WHERE e.user_id = 1 AND e.status = 'active';
```

**Find courses user can access**:
```sql
-- Free courses (always accessible)
SELECT * FROM courses WHERE category = 'free';

-- Alacarte courses user owns
SELECT DISTINCT c.*
FROM courses c
JOIN entitlements e ON c.stripe_product_id = (
    SELECT product_id FROM stripe_prices WHERE id = e.stripe_price_id
)
WHERE e.user_id = 1
  AND e.status = 'active'
  AND c.category IN ('alacarte', 'unique');

-- Curriculum courses (if user owns ANY curriculum product)
SELECT c.*
FROM courses c
WHERE c.category = 'curriculum'
  AND EXISTS (
    SELECT 1 FROM entitlements e
    JOIN stripe_prices sp ON e.stripe_price_id = sp.id
    JOIN stripe_products spr ON sp.product_id = spr.id
    WHERE e.user_id = 1
      AND e.status = 'active'
      AND spr.category = 'curriculum'
  );
```

**Check idempotency for payment intent**:
```sql
SELECT * FROM entitlements
WHERE stripe_payment_intent_id = 'pi_test_12345';
-- Should return 0 or 1 row (never 2+)
```
```

**Acceptance Criteria**:
- New "Database Schema Overview" section added after Overview
- Includes ASCII diagram showing all relationships
- Includes "Critical Fields Explained" table
- Includes "Access Control Flow" diagram
- Includes "Common Schema-Related Bugs" table
- Includes SQL query examples

**Testing**:
- Read file to verify section was added
- Verify markdown formatting is correct
- Check ASCII diagrams render properly in markdown viewer

**Evidence Required**:
- File path: `/app/docs/testing/STRIPE_TESTING.md`
- Line numbers where section starts and ends
- Confirmation all diagrams and tables are present

---

### Item 5: Add Error Code Reference Table to STRIPE_TESTING.md

**Issue**: When developers encounter errors during testing, they have to dig through code to understand what went wrong. A quick reference table would speed up debugging.

**Why Critical**: Faster debugging = faster development. Clear error messages improve developer experience.

**File to Modify**: `/app/docs/testing/STRIPE_TESTING.md`

**Implementation**:

Add this new section after the "Common Issues" section (around line 470):

```markdown
## Error Code Reference

Quick reference for all error responses from the Stripe payment API.

### Checkout Session Errors

| HTTP Status | Error Message | Cause | Fix |
|-------------|---------------|-------|-----|
| 404 | `Product not found` | `product_id` doesn't exist in database | Verify product exists: `SELECT * FROM stripe_products WHERE id = 'prod_xxx'` |
| 400 | `User employment status not found. Please complete your profile.` | User has no `UserExperience` record or `employment_status` is NULL | Create profile: `INSERT INTO user_experience (user_id, employment_status, name) VALUES (...)` |
| 400 | `No price available for employment status: {status}` | No price exists with matching `eligible_employment_statuses` | Add price or update metadata: `UPDATE stripe_prices SET stripe_metadata = '{"eligible_employment_statuses": [...]}' WHERE id = 'price_xxx'` |
| 400 | `Invalid referrer code` | Referrer code doesn't match any user's referral code | Verify referrer exists: `SELECT * FROM users WHERE referral_code = 'XXX'` |
| 400 | `Cannot use your own referral code` | User tried to refer themselves | Use different referral code |
| 400 | `No active prices found for this product` | Product exists but has no active prices | Check: `SELECT * FROM stripe_prices WHERE product_id = 'prod_xxx' AND active = true` |
| 500 | `Failed to create checkout session: {stripe_error}` | Stripe API error | Check Stripe dashboard for details, verify API keys |

### Webhook Errors

| HTTP Status | Error Message | Cause | Fix |
|-------------|---------------|-------|-----|
| 400 | `Invalid JSON` | Webhook payload is malformed | Check raw request body format |
| 400 | `Invalid signature` | Webhook signature verification failed | Verify `STRIPE_WEBHOOK_SECRET` matches Stripe CLI or dashboard |
| 200 (with error status) | `{"status": "error", "message": "Missing metadata"}` | `payment_intent.metadata` missing `user_id` or `price_id` | Verify `payment_intent_data` passed in checkout session creation |
| 200 (with error status) | `{"status": "error", "message": "Database error"}` | Exception during entitlement creation | Check backend logs for stack trace |

### Access Control Errors

| Scenario | Behavior | Cause | Fix |
|----------|----------|-------|-----|
| User can't access purchased course | `check_course_access()` returns `False` | Entitlement status is "refunded" OR no entitlement exists | Check: `SELECT * FROM entitlements WHERE user_id = X AND stripe_price_id = 'price_xxx'` |
| Alacarte course locked despite payment | Access denied after purchase | `courses.stripe_product_id` is NULL | Update: `UPDATE courses SET stripe_product_id = 'prod_xxx' WHERE id = Y` |
| Buying one alacarte unlocks all | Access granted to wrong courses | `courses.stripe_product_id` not set correctly OR access logic bug | Verify each course has unique `stripe_product_id` for alacarte |
| Curriculum course locked despite bundle purchase | No curriculum access | Purchased product has wrong category OR no entitlement created | Check: `SELECT category FROM stripe_products WHERE id = 'prod_xxx'` (should be "curriculum") |

### Database Constraint Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `UNIQUE constraint failed: entitlements.stripe_payment_intent_id` | Trying to create entitlement with duplicate `payment_intent_id` | This is EXPECTED for idempotency - webhook handler should catch and return existing entitlement |
| `FOREIGN KEY constraint failed` (stripe_price_id) | Trying to create entitlement for non-existent price | Verify price exists: `SELECT * FROM stripe_prices WHERE id = 'price_xxx'` |
| `NOT NULL constraint failed: user_experience.employment_status` | Trying to save UserExperience without employment_status | Set employment_status when creating profile |

### Stripe API Errors

| Stripe Error Code | Meaning | Resolution |
|-------------------|---------|------------|
| `resource_missing` | Product or price doesn't exist in Stripe | Run `create_test_products.py` or create in Stripe dashboard |
| `invalid_request_error` | Malformed API request | Check Stripe API logs in dashboard |
| `api_key_expired` | Invalid or expired API key | Regenerate API key in Stripe dashboard |
| `testmode_charges_only` | Trying to charge live card in test mode | Use test card `4242 4242 4242 4242` |
| `card_declined` | Payment declined by card network | Use successful test card or check decline reason |

### Frontend Error Messages

Expected user-facing error messages (for frontend implementation):

| User Action | Error Scenario | Expected Message |
|-------------|----------------|------------------|
| Click "Unlock Course" | No employment status | "Please complete your profile before purchasing" |
| Click "Unlock Course" | Network error | "Unable to create checkout session. Please try again." |
| Click "Unlock Course" | Invalid product | "This course is not available for purchase. Please contact support." |
| Complete Stripe checkout | Webhook fails | "Payment processed, but access not granted yet. Please refresh in 1 minute or contact support." |
| Use referral code | Invalid code | "Invalid referral code. Please check and try again." |
| Use referral code | Self-referral | "You cannot use your own referral code." |

### Debugging Workflow

**Problem**: Course remains locked after payment

**Steps**:
1. Check webhook delivery:
   ```bash
   # In Stripe CLI output
   --> payment_intent.succeeded [200]  ✅ Delivered
   --> payment_intent.succeeded [400]  ❌ Failed
   ```

2. Check backend logs:
   ```
   INFO: Received webhook event: payment_intent.succeeded
   INFO: Granted entitlement for user 1, price price_xxx  ✅ Success
   ERROR: Missing metadata in payment intent pi_xxx  ❌ Failed
   ```

3. Check database:
   ```sql
   SELECT * FROM entitlements
   WHERE user_id = 1
   ORDER BY created_at DESC
   LIMIT 1;

   -- No rows = webhook didn't create entitlement
   -- status='refunded' = payment was refunded
   -- status='active' = entitlement exists, frontend issue
   ```

4. Check frontend refetch:
   - Open browser DevTools → Network tab
   - After redirect from Stripe, look for GET `/api/payments/entitlements`
   - If missing, frontend isn't refetching after purchase

**Problem**: Wrong price displayed at checkout

**Steps**:
1. Check user's employment status:
   ```sql
   SELECT employment_status
   FROM user_experience
   WHERE user_id = 1;
   -- NULL = Error: "Please complete profile"
   -- "Student" = Should show student rate
   ```

2. Check price metadata:
   ```sql
   SELECT
       id,
       amount,
       stripe_metadata->>'eligible_employment_statuses' as eligible
   FROM stripe_prices
   WHERE product_id = 'prod_xxx';

   -- Verify user's employment status is in eligible array
   ```

3. Check backend logs:
   ```
   INFO: Created checkout session for user 1, price price_xxx ($97.00)
   -- Verify price_id and amount match expectations
   ```
```

**Acceptance Criteria**:
- New "Error Code Reference" section added
- Includes 5 tables: Checkout Session Errors, Webhook Errors, Access Control Errors, Database Constraint Errors, Stripe API Errors
- Includes "Frontend Error Messages" table
- Includes "Debugging Workflow" section with SQL examples

**Testing**:
- Read file to verify section was added
- Verify all tables format correctly
- Verify SQL examples are syntactically correct

**Evidence Required**:
- File path: `/app/docs/testing/STRIPE_TESTING.md`
- Line numbers where section was added
- Confirmation all 5 tables are present

---

## 🟡 MEDIUM PRIORITY ITEMS (6-10)

### Item 6: Add Referral Flow to E2E Test Markdown

**Issue**: The E2E test markdown doesn't cover the referral system (25% credit to referrer), which is a core feature of the payment flow.

**Why Important**: Referral system directly impacts revenue and user acquisition. Needs thorough E2E testing.

**File to Modify**: `/.claude/commands/e2e/test_stripe_checkout.md`

**Implementation**:

Add this new section after "### 10. API Verification (Optional)" (around line 150):

```markdown
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
```

**Acceptance Criteria**:
- New section "11. Referral Flow Testing" added to E2E test
- Includes 6 subsections: Setup, Purchase, Verify Access, Verify Credit, API Verification, Database Verification
- Includes 3 edge cases: Self-referral, Invalid code, Optional code
- Includes success criteria checklist
- Numbered steps continue from previous section (54-107)

**Testing**:
- Read file to verify section was added correctly
- Verify markdown formatting is correct
- Check step numbers are sequential

**Evidence Required**:
- File path: `/.claude/commands/e2e/test_stripe_checkout.md`
- Line numbers where section was added
- Confirmation all 6 subsections and 3 edge cases are present

---

### Item 7: Add Invalid Employment Status Test

**Issue**: The code checks `if employment_status in eligible_statuses` but we never test what happens when a user has garbage data like `"INVALID_STATUS"` or `"123"`.

**Why Important**: Prevents unexpected behavior with corrupted or imported data.

**File to Modify**: `/app/server/tests/test_payments.py`

**Implementation**:

Add this test after line 211 (after `test_checkout_selects_price_based_on_employment_status`):

```python
@pytest.mark.asyncio
async def test_checkout_rejects_invalid_employment_status(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout rejects invalid employment status."""
    # Create product with employment-based pricing
    product = StripeProduct(
        id="prod_invalid_emp_test",
        name="Test Course",
        category="curriculum",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    # Create prices with valid employment status metadata
    employed_price = StripePrice(
        id="price_employed_invalid_test",
        product_id=product.id,
        amount=49700,
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Employed Rate",
            "eligible_employment_statuses": ["Employed full-time", "Employed part-time"]
        }
    )
    student_price = StripePrice(
        id="price_student_invalid_test",
        product_id=product.id,
        amount=9700,
        currency="usd",
        active=True,
        stripe_metadata={
            "price_name": "Student Rate",
            "eligible_employment_statuses": ["Student", "Between jobs"]
        }
    )
    test_db.add(employed_price)
    test_db.add(student_price)
    await test_db.commit()

    # Set user employment status to INVALID value
    experience_result = await test_db.execute(
        select(UserExperience).where(UserExperience.user_id == override_get_current_user.id)
    )
    user_experience = experience_result.scalar_one_or_none()
    if user_experience:
        user_experience.employment_status = "GARBAGE_INVALID_STATUS_123"
    else:
        user_experience = UserExperience(
            user_id=override_get_current_user.id,
            employment_status="GARBAGE_INVALID_STATUS_123",
            name="Test User",
        )
        test_db.add(user_experience)
    await test_db.commit()

    # Attempt checkout
    response = client.post(
        "/api/payments/checkout",
        json={"product_id": "prod_invalid_emp_test", "referrer_code": None},
    )

    # Should return 400 error
    assert response.status_code == 400
    assert "No price available for employment status" in response.json()["detail"]
    assert "GARBAGE_INVALID_STATUS_123" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_rejects_empty_employment_status(client, override_get_current_user, test_db):
    """Test POST /api/payments/checkout rejects empty string employment status."""
    # Create product and prices
    product = StripeProduct(
        id="prod_empty_emp_test",
        name="Test Course",
        category="alacarte",
        active=True,
    )
    test_db.add(product)
    await test_db.flush()

    price = StripePrice(
        id="price_empty_emp_test",
        product_id=product.id,
        amount=1000,
        currency="usd",
        active=True,
        stripe_metadata={
            "eligible_employment_statuses": ["Student"]
        }
    )
    test_db.add(price)
    await test_db.commit()

    # Set employment status to empty string
    experience_result = await test_db.execute(
        select(UserExperience).where(UserExperience.user_id == override_get_current_user.id)
    )
    user_experience = experience_result.scalar_one_or_none()
    if user_experience:
        user_experience.employment_status = ""  # Empty string
    else:
        user_experience = UserExperience(
            user_id=override_get_current_user.id,
            employment_status="",
            name="Test User",
        )
        test_db.add(user_experience)
    await test_db.commit()

    # Attempt checkout
    response = client.post(
        "/api/payments/checkout",
        json={"product_id": "prod_empty_emp_test", "referrer_code": None},
    )

    # Should return 400 error
    assert response.status_code == 400
    assert "No price available for employment status" in response.json()["detail"]
```

**Acceptance Criteria**:
- Two tests added: invalid status and empty string
- Both tests return 400 with clear error message
- All existing payment tests still pass

**Testing**:
```bash
cd /app/server
uv run pytest tests/test_payments.py::test_checkout_rejects_invalid_employment_status -v
uv run pytest tests/test_payments.py::test_checkout_rejects_empty_employment_status -v
uv run pytest tests/test_payments.py -v  # Verify no regressions (should be 22 tests now)
```

**Evidence Required**:
- File path and line numbers where tests were added
- Terminal output showing both tests passed
- Confirmation total test count increased to 22

---

### Item 8: Add Manual Product Creation Guide to STRIPE_TESTING.md

**Issue**: The documentation only covers creating products via script (`create_test_products.py`). Non-technical users or those debugging need to know how to create products manually in Stripe Dashboard.

**Why Important**: Enables manual setup, debugging, and understanding of what the script does.

**File to Modify**: `/app/docs/testing/STRIPE_TESTING.md`

**Implementation**:

Add this new section after "## Environment Setup" section (around line 70):

```markdown
## Manual Product & Price Creation

This section covers creating products and prices manually in Stripe Dashboard. Use this for:
- Understanding what `create_test_products.py` script does
- Debugging product/price setup issues
- Creating products in live mode
- One-off product creation

### Step 1: Create Product in Stripe Dashboard

1. Login to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Ensure you're in **Test Mode** (toggle at top of page)
3. Navigate to: **Products** → **Add product**
4. Fill in product details:
   - **Name**: `AI in 4 Weekends - Full Curriculum`
   - **Description**: `Complete AI mastery program covering all fundamentals`
   - **Image**: (optional)
   - **Metadata** (optional):
     - Key: `category`, Value: `curriculum`
5. **Do NOT add prices yet** (we'll add them manually next)
6. Click **Add product**
7. **Copy the Product ID** (format: `prod_xxxxxxxxxxxxx`)
   - Found at top of product page
   - Example: `prod_TCmV2iBHlH5fCL`

### Step 2: Add Employment-Based Prices

**CRITICAL**: Each product needs TWO prices (student rate + employed rate)

#### Price 1: Student/Reduced Rate

1. On the product page, click **Add another price**
2. Configure price:
   - **Price model**: One time
   - **Price**: `$97.00` (for curriculum) or `$9.00` (for alacarte)
   - **Currency**: USD
   - **Description** (optional): `Student/Reduced Rate`
3. Click **Advanced options**
4. **Add metadata**:
   - Key: `price_name`
   - Value: `AI in 4 Weekends - Student/Reduced Rate`
5. **Add metadata** (CRITICAL for price selection):
   - Key: `eligible_employment_statuses`
   - Value: `["Student", "Between jobs", "Homemaker", "Retired", "Other"]`
   - ⚠️ **Must be valid JSON array format** (including quotes and brackets)
6. Click **Add price**
7. **Copy the Price ID** (format: `price_xxxxxxxxxxxxx`)
   - Example: `price_1QxdofABC123xyz`

#### Price 2: Employed Rate

1. Click **Add another price** again
2. Configure price:
   - **Price model**: One time
   - **Price**: `$497.00` (for curriculum) or `$97.00` (for alacarte)
   - **Currency**: USD
   - **Description** (optional): `Employed Rate`
3. Click **Advanced options**
4. **Add metadata**:
   - Key: `price_name`
   - Value: `AI in 4 Weekends - Employed Rate`
5. **Add metadata** (CRITICAL):
   - Key: `eligible_employment_statuses`
   - Value: `["Employed full-time", "Employed part-time", "Self-employed/Freelancer"]`
6. Click **Add price**
7. **Copy the Price ID**

### Step 3: Update Database with Product/Price IDs

**Update stripe_products table**:
```sql
INSERT INTO stripe_products (id, name, description, category, active, updated_at)
VALUES (
    'prod_TCmV2iBHlH5fCL',  -- Replace with your product ID
    'AI in 4 Weekends - Full Curriculum',
    'Complete AI mastery program',
    'curriculum',
    1,
    CURRENT_TIMESTAMP
);
```

**Update stripe_prices table** (for EACH price):
```sql
-- Student Rate
INSERT INTO stripe_prices (
    id,
    product_id,
    amount,
    currency,
    active,
    stripe_metadata,
    updated_at
)
VALUES (
    'price_1QxdofStudent123',  -- Replace with your price ID
    'prod_TCmV2iBHlH5fCL',     -- Replace with your product ID
    9700,                       -- $97.00 in cents
    'usd',
    1,
    '{"price_name": "Student Rate", "eligible_employment_statuses": ["Student", "Between jobs", "Homemaker", "Retired", "Other"]}',
    CURRENT_TIMESTAMP
);

-- Employed Rate
INSERT INTO stripe_prices (
    id,
    product_id,
    amount,
    currency,
    active,
    stripe_metadata,
    updated_at
)
VALUES (
    'price_1QxdofEmployed456',  -- Replace with your price ID
    'prod_TCmV2iBHlH5fCL',      -- Replace with your product ID
    49700,                       -- $497.00 in cents
    'usd',
    1,
    '{"price_name": "Employed Rate", "eligible_employment_statuses": ["Employed full-time", "Employed part-time", "Self-employed/Freelancer"]}',
    CURRENT_TIMESTAMP
);
```

### Step 4: Link Courses to Products

**For Curriculum Courses** (ALL curriculum courses share ONE product):
```sql
UPDATE courses
SET stripe_product_id = 'prod_TCmV2iBHlH5fCL'  -- Replace with your product ID
WHERE category = 'curriculum';
```

**For Alacarte Courses** (EACH course gets unique product):
```sql
-- Prompt Engineering course
UPDATE courses
SET stripe_product_id = 'prod_PromptEngXXXXX'  -- Replace with product ID
WHERE title = 'Prompt Engineering Mastery';

-- AI Automation course
UPDATE courses
SET stripe_product_id = 'prod_AIAutomationXXX'  -- Replace with product ID
WHERE title = 'AI Automation for Business';
```

### Step 5: Verify Setup

**Test price selection logic**:
```bash
cd /app/server
uv run python -c "
from sqlalchemy import create_engine, select
from db.models import StripeProduct, StripePrice
import json

engine = create_engine('sqlite:///./db/database.db')
with engine.connect() as conn:
    # Get product
    result = conn.execute(
        select(StripeProduct).where(StripeProduct.id == 'prod_TCmV2iBHlH5fCL')
    )
    product = result.fetchone()
    print(f'Product: {product.name}')

    # Get prices
    result = conn.execute(
        select(StripePrice).where(StripePrice.product_id == 'prod_TCmV2iBHlH5fCL')
    )
    prices = result.fetchall()

    for price in prices:
        metadata = json.loads(price.stripe_metadata)
        eligible = metadata.get('eligible_employment_statuses', [])
        print(f'  Price: \${price.amount/100:.2f} - Eligible: {eligible}')
"
```

Expected output:
```
Product: AI in 4 Weekends - Full Curriculum
  Price: $97.00 - Eligible: ['Student', 'Between jobs', 'Homemaker', 'Retired', 'Other']
  Price: $497.00 - Eligible: ['Employed full-time', 'Employed part-time', 'Self-employed/Freelancer']
```

### Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| **Metadata not JSON array** | Price not selected for any user | Use `["Student", "Other"]` not `Student, Other` |
| **Missing quotes in metadata** | JSON parse error | Use `["Student"]` not `[Student]` |
| **Wrong amount format** | Price shows as $970.00 instead of $97.00 | Use cents: 9700 = $97.00 |
| **Forgot to link course** | `courses.stripe_product_id` is NULL | Run UPDATE query to set product_id |
| **Used live mode product ID in test mode** | 404 Product not found | Ensure dashboard toggle is set to Test Mode |

### Pricing Recommendations

| Course Type | Student Rate | Employed Rate | Rationale |
|-------------|--------------|---------------|-----------|
| Free Intro | $0 | $0 | No payment required |
| Alacarte (short) | $9 | $97 | ~10x markup for employed |
| Alacarte (comprehensive) | $49 | $197 | ~4x markup |
| Full Curriculum Bundle | $97 | $497 | ~5x markup, best value for employed |

### Metadata Fields Reference

**Product Metadata** (optional):
- `category`: "free" \| "alacarte" \| "curriculum" \| "unique"
- Used for filtering/reporting (not required for access control)

**Price Metadata** (REQUIRED):
- `price_name`: Human-readable price name (displayed in admin)
- `eligible_employment_statuses`: JSON array of employment statuses that can access this price

**Valid Employment Statuses**:
- `"Student"`
- `"Between jobs"`
- `"Homemaker"`
- `"Retired"`
- `"Other"`
- `"Employed full-time"`
- `"Employed part-time"`
- `"Self-employed/Freelancer"`

⚠️ **Case-sensitive**: Must match exactly (including spaces and capitalization)
```

**Acceptance Criteria**:
- New "Manual Product & Price Creation" section added after Environment Setup
- Includes 5 steps with detailed instructions
- Includes verification script
- Includes "Common Mistakes" table
- Includes "Pricing Recommendations" table
- Includes "Metadata Fields Reference"

**Testing**:
- Read file to verify section was added
- Verify SQL examples are syntactically correct
- Verify Python verification script runs without errors

**Evidence Required**:
- File path: `/app/docs/testing/STRIPE_TESTING.md`
- Line numbers where section was added
- Confirmation all 5 steps and tables are present

---

### Item 9: Add Production Deployment Checklist to STRIPE_TESTING.md

**Issue**: Documentation focuses on test mode but doesn't cover production deployment steps. Critical security and configuration items could be missed.

**Why Important**: Prevents production security vulnerabilities and configuration errors.

**File to Modify**: `/app/docs/testing/STRIPE_TESTING.md`

**Implementation**:

This section was already added in Item 3 as part of the security considerations. Verify it exists and is complete.

If the section was not fully added in Item 3, add this after the "CRITICAL SECURITY CONSIDERATIONS" section:

```markdown
## Production Deployment Guide

### Pre-Deployment Checklist

Complete this checklist BEFORE deploying to production:

#### Security Requirements
- [ ] Webhook signature verification enabled (`payments.py:197` uncommented)
- [ ] `stripe_service.verify_webhook_signature()` implemented and tested
- [ ] Test coverage added for invalid webhook signatures
- [ ] `STRIPE_SECRET_KEY` stored in secure secrets manager (not .env file)
- [ ] `STRIPE_WEBHOOK_SECRET` stored in secure secrets manager
- [ ] API keys rotated if ever committed to git history
- [ ] CORS configured to only allow frontend domain
- [ ] Rate limiting enabled on checkout endpoint (prevent DDoS)
- [ ] Logging sanitized (no API keys or PII in logs)
- [ ] Database connection uses SSL/TLS
- [ ] SQL injection protection verified (use parameterized queries)

#### Stripe Configuration
- [ ] Stripe account verified (business info submitted)
- [ ] Bank account connected for payouts
- [ ] Tax settings configured
- [ ] Products created in **live mode** (not test mode)
- [ ] Prices created with correct amounts (double-check cents vs dollars)
- [ ] Webhook endpoint added in Stripe dashboard
- [ ] Webhook events selected: `payment_intent.succeeded`
- [ ] Webhook signing secret copied to production secrets
- [ ] Test payment completed in live mode (use real card, then refund)
- [ ] Live mode API keys (sk_live_..., pk_live_...) configured

#### Database
- [ ] Live mode product IDs inserted into `stripe_products` table
- [ ] Live mode price IDs inserted into `stripe_prices` table
- [ ] All courses have `stripe_product_id` set (except free courses)
- [ ] Employment statuses in metadata match exactly
- [ ] Database backups enabled
- [ ] Migration scripts run successfully
- [ ] Foreign key constraints verified

#### Application Configuration
- [ ] `STRIPE_TEST_MODE=false` in production .env
- [ ] `FRONTEND_URL` set to production domain (https://yourdomain.com)
- [ ] `BACKEND_URL` set to production API domain
- [ ] Email service configured for magic links
- [ ] Error monitoring enabled (Sentry, etc.)
- [ ] Application logs configured
- [ ] Health check endpoint responding

#### Testing in Production
- [ ] Create test user with real email
- [ ] Complete profile with employment status
- [ ] Purchase course with REAL card (small amount like $1)
- [ ] Verify webhook delivered successfully
- [ ] Verify entitlement granted in database
- [ ] Verify course unlocked in UI
- [ ] Verify email notifications sent (if implemented)
- [ ] Refund test payment in Stripe dashboard
- [ ] Verify refund reflected in database (status = "refunded")
- [ ] Verify user loses access after refund
- [ ] Test referral flow with real users

#### Monitoring & Alerts
- [ ] Webhook failure alerts configured
- [ ] Payment failure alerts configured
- [ ] Database error alerts configured
- [ ] Daily transaction report set up
- [ ] Stripe dashboard bookmarked for monitoring

### Live Mode Transition Steps

**Step 1: Create Live Mode Products**

Option A: Manually via Dashboard (see "Manual Product Creation" section)

Option B: Script (modify `create_test_products.py`):
```python
# Change Stripe API key to live mode
stripe.api_key = "sk_live_51..."  # ⚠️ USE LIVE KEY

# Run script to create products
# WARNING: This will create REAL products in your Stripe account
```

**Step 2: Update Environment Variables**

```bash
# .env.production
STRIPE_SECRET_KEY=sk_live_51...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...  # From live webhook endpoint
STRIPE_TEST_MODE=false
FRONTEND_URL=https://yourdomain.com
```

**Step 3: Configure Production Webhook**

1. Stripe Dashboard → **Developers** → **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL**: `https://yourdomain.com/api/payments/webhook`
4. **Events to send**:
   - ✅ `payment_intent.succeeded`
   - ✅ `payment_intent.payment_failed` (optional, for error handling)
   - ✅ `charge.refunded` (optional, for refund handling)
5. Click **Add endpoint**
6. **Copy signing secret** (`whsec_...`) to production secrets manager

**Step 4: Test Small Transaction**

```bash
# Use REAL credit card (Visa ending in 4242 does NOT work in live mode)
# Charge minimum amount (e.g., $1.00)
# Check Stripe dashboard for payment success
# Verify webhook delivered: Developers → Webhooks → endpoint → Logs
# Check database for entitlement creation
# Refund the test payment: Payments → [payment] → Refund
```

**Step 5: Monitor First 24 Hours**

- Check Stripe dashboard every 2-4 hours
- Monitor webhook delivery success rate (should be 100%)
- Check error logs for exceptions
- Verify entitlements created for all payments
- Test frontend purchase flow multiple times

### Rollback Plan

If critical issues discovered in production:

1. **Immediate**: Set `STRIPE_TEST_MODE=true` to stop live charges
2. **Disable checkout**: Set feature flag or disable "Unlock Course" buttons
3. **Communicate**: Notify users via banner or email
4. **Investigate**: Check logs, webhooks, database
5. **Fix**: Deploy fix to staging first
6. **Re-enable**: Gradually re-enable after verification

### Production Support Checklist

- [ ] Support email configured (support@yourdomain.com)
- [ ] Refund policy documented and linked on checkout page
- [ ] Terms of service includes payment terms
- [ ] Privacy policy includes payment data handling
- [ ] Customer support trained on payment issues
- [ ] Stripe dashboard access granted to support team (read-only)
- [ ] Runbook created for common payment issues

### Compliance Requirements

**PCI DSS Compliance**:
- ✅ No credit card data stored in your database
- ✅ All payments processed by Stripe (PCI-compliant)
- ✅ Only store Stripe customer/payment IDs (not card numbers)

**GDPR Compliance** (if EU customers):
- [ ] Privacy policy includes Stripe data processing
- [ ] Data retention policy defined
- [ ] User data export includes entitlements
- [ ] User deletion includes Stripe customer deletion

**Tax Compliance**:
- [ ] Sales tax configuration in Stripe
- [ ] Tax ID collection for business customers (if required)
- [ ] Invoice generation includes tax breakdown

### Post-Launch Monitoring

**Daily** (first week):
- Check webhook delivery rate
- Review failed payments
- Check refund requests
- Monitor database growth

**Weekly** (ongoing):
- Review revenue metrics
- Analyze conversion rates
- Check referral program effectiveness
- Review customer support tickets

**Monthly**:
- Reconcile Stripe payouts with bank deposits
- Review Stripe fees
- Analyze pricing tier usage
- Update documentation based on issues encountered
```

**Acceptance Criteria**:
- Section exists and is complete (may have been added in Item 3)
- Includes pre-deployment checklist with 40+ items
- Includes live mode transition steps
- Includes rollback plan
- Includes compliance requirements
- Includes monitoring schedule

**Testing**:
- Read file to verify section exists
- Verify all checklists are present
- Count checklist items (should be 40+)

**Evidence Required**:
- File path: `/app/docs/testing/STRIPE_TESTING.md`
- Line numbers where section was added (or exists)
- Confirmation section is complete with all subsections

---

### Item 10: Add Test Data Cleanup Section to STRIPE_TESTING.md

**Issue**: After running tests multiple times, test data accumulates in database and Stripe dashboard. Developers need guidance on cleanup procedures.

**Why Important**: Clean test environment prevents false positives and makes debugging easier.

**File to Modify**: `/app/docs/testing/STRIPE_TESTING.md`

**Implementation**:

Add this new section after "## Unit Testing" section (around line 310):

```markdown
## Test Data Cleanup

Maintaining a clean test environment ensures reliable test results and easier debugging.

### Database Cleanup

#### Option 1: Full Database Reset (Nuclear Option)

Use this when you want a completely fresh database:

```bash
cd /app/server

# Backup current database (optional)
cp db/database.db db/database.backup.db

# Delete database
rm db/database.db

# Recreate database with migrations
uv run alembic upgrade head

# Seed with initial data
uv run python db/seed_db.py

# Create test mode Stripe products
uv run python create_test_products.py
```

**When to use**:
- After switching between test and live mode
- When schema migrations were applied
- When test data is completely corrupted
- Before important E2E testing session

#### Option 2: Selective Cleanup (Surgical Option)

Remove only test-related data:

```sql
-- Delete test entitlements
DELETE FROM entitlements
WHERE user_id IN (
    SELECT id FROM users WHERE email LIKE '%@example.com'
);

-- Delete test referrals
DELETE FROM referrals
WHERE referrer_id IN (
    SELECT id FROM users WHERE email LIKE '%@example.com'
);

-- Delete test users
DELETE FROM user_experience
WHERE user_id IN (
    SELECT id FROM users WHERE email LIKE '%@example.com'
);

DELETE FROM users
WHERE email LIKE '%@example.com';

-- Delete test magic links
DELETE FROM magic_links
WHERE created_at < datetime('now', '-1 day');
```

**When to use**:
- Between E2E test runs
- When preserving production-like data
- When testing specific scenarios repeatedly

#### Option 3: Pytest Automatic Cleanup (Recommended for Unit Tests)

Your `conftest.py` already handles this ✅:

```python
@pytest.fixture
async def test_db():
    """Provide test database with automatic rollback."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()  # Automatic cleanup!
```

**How it works**:
- Each test runs in a transaction
- Transaction is rolled back after test completes
- Database returns to clean state automatically
- No manual cleanup needed

**Verify it's working**:
```bash
# Run test that creates entitlement
uv run pytest tests/test_entitlement_service.py::test_grant_entitlement -v

# Check database (should be empty)
sqlite3 db/database.db "SELECT COUNT(*) FROM entitlements;"
# Output: 0 (rolled back!)
```

### Stripe Test Mode Cleanup

#### View Test Data in Dashboard

1. Login to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Toggle to **Test Mode** (top right)
3. **Payments**: View all test payment intents
4. **Customers**: View test customers (if creating them)
5. **Webhooks**: View webhook delivery logs

#### Cleanup Test Payment Intents

**Method 1: Stripe Dashboard**
1. Navigate to **Payments**
2. Select test payments
3. Click **Archive** (does not delete, just hides)

**Method 2: Stripe CLI**
```bash
# List recent test payments
stripe payment_intents list --limit 10

# Cancel uncaptured payment intent
stripe payment_intents cancel pi_test_12345
```

**Method 3: Python Script**

Create `/app/server/cleanup_stripe_test_data.py`:

```python
#!/usr/bin/env python3
"""Cleanup test mode Stripe data."""
import stripe
from core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# List and archive old test payment intents
print("Archiving old test payment intents...")
payment_intents = stripe.PaymentIntent.list(limit=100)
archived_count = 0

for pi in payment_intents.auto_paging_iter():
    # Only archive succeeded/canceled payments (not pending)
    if pi.status in ['succeeded', 'canceled']:
        try:
            # Note: Stripe doesn't allow deletion, only archiving
            # Archiving removes from default views
            print(f"Archiving {pi.id} ({pi.amount/100:.2f} {pi.currency})")
            archived_count += 1
        except stripe.StripeError as e:
            print(f"Error archiving {pi.id}: {e}")

print(f"Archived {archived_count} payment intents")

# Note: Test mode data is automatically deleted after 90 days
```

Run cleanup:
```bash
cd /app/server
uv run python cleanup_stripe_test_data.py
```

#### Automatic Cleanup (Stripe Feature)

Stripe automatically deletes test mode data after **90 days**.

No manual cleanup needed for long-term maintenance.

### Cleanup Between E2E Test Runs

**Before each E2E test session**:

```bash
#!/bin/bash
# cleanup_e2e_env.sh

echo "🧹 Cleaning E2E test environment..."

# 1. Reset database
cd /app/server
rm db/database.db
uv run alembic upgrade head
uv run python db/seed_db.py
uv run python create_test_products.py

# 2. Clear backend cache (if using Redis)
# redis-cli FLUSHDB

# 3. Clear frontend build cache
cd /app/client
rm -rf node_modules/.cache
rm -rf .vite

echo "✅ E2E environment cleaned"
```

Make executable and run:
```bash
chmod +x cleanup_e2e_env.sh
./cleanup_e2e_env.sh
```

### Cleanup Checklist

**After each development session**:
- [ ] Delete test users created manually
- [ ] Archive test payment intents in Stripe dashboard
- [ ] Clear test entitlements from database
- [ ] Clear browser localStorage (for frontend tests)

**Weekly maintenance**:
- [ ] Full database reset
- [ ] Review Stripe test mode webhook logs
- [ ] Delete old Stripe test products (if many exist)
- [ ] Backup production database

**Before E2E testing**:
- [ ] Run database reset
- [ ] Verify Stripe CLI connected
- [ ] Clear browser cache and cookies
- [ ] Restart backend server
- [ ] Restart frontend dev server

### Verification Queries

**Check for test data leakage**:

```sql
-- Test users that should be cleaned up
SELECT email, created_at
FROM users
WHERE email LIKE '%@example.com%'
ORDER BY created_at DESC;

-- Orphaned entitlements (no user)
SELECT e.id, e.stripe_payment_intent_id
FROM entitlements e
LEFT JOIN users u ON e.user_id = u.id
WHERE u.id IS NULL;

-- Duplicate payment intents (idempotency check)
SELECT stripe_payment_intent_id, COUNT(*) as count
FROM entitlements
GROUP BY stripe_payment_intent_id
HAVING count > 1;

-- Referrals with missing referee
SELECT r.id, r.referee_email
FROM referrals r
WHERE r.referee_email NOT IN (SELECT email FROM users);
```

Expected result: All queries return **0 rows** in clean environment.

### Troubleshooting Cleanup Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Can't delete database file | File in use by running process | Stop backend server, then delete |
| Foreign key constraint error | Trying to delete parent before children | Delete in order: entitlements → referrals → user_experience → users |
| Pytest tests still see old data | Not using test_db fixture | Ensure test function has `test_db: AsyncSession` parameter |
| Stripe dashboard shows 1000+ test payments | Never archived old data | Run cleanup script or wait 90 days |
| Database grows to 100+ MB | Accumulated test data | Run full database reset |

### Automated Cleanup with Git Hooks

Create `.git/hooks/pre-push`:

```bash
#!/bin/bash
# Auto-cleanup before pushing code

echo "Running pre-push cleanup..."

cd app/server
uv run pytest tests/ -x || exit 1  # Run tests, exit on first failure

# If tests passed, cleanup is already done by pytest fixtures
echo "✅ Tests passed, test data automatically cleaned up"
```

Make executable:
```bash
chmod +x .git/hooks/pre-push
```

Now cleanup happens automatically before every `git push`.
```

**Acceptance Criteria**:
- New "Test Data Cleanup" section added after Unit Testing section
- Includes 3 database cleanup options
- Includes Stripe cleanup methods
- Includes cleanup scripts (bash and Python)
- Includes verification queries
- Includes troubleshooting table

**Testing**:
- Read file to verify section was added
- Verify SQL queries are syntactically correct
- Test bash script syntax: `bash -n cleanup_e2e_env.sh`

**Evidence Required**:
- File path: `/app/docs/testing/STRIPE_TESTING.md`
- Line numbers where section was added
- Confirmation all subsections are present

---

## 📝 LOW PRIORITY ITEMS (11-13)

### Item 11: Add Frontend Unit Test Placeholder for CourseCard

**Issue**: There are zero frontend tests for the CourseCard component's checkout flow. This is a gap in test coverage, but frontend tests are lower priority than backend tests.

**Why Low Priority**: E2E tests cover the full flow. Frontend unit tests are "nice to have" but not critical.

**File to Create**: `/app/client/src/components/courses/CourseCard.test.tsx`

**Implementation**:

Create a placeholder test file with TODO comments:

```typescript
/**
 * Frontend Unit Tests for CourseCard Checkout Flow
 *
 * TODO: Implement these tests using Vitest + React Testing Library
 *
 * Test Coverage Needed:
 * 1. Locked state for courses without entitlement
 * 2. Unlocked state for courses with entitlement
 * 3. Price display based on user employment status
 * 4. Checkout button click initiates API call
 * 5. Loading state during checkout
 * 6. Error handling for API failures
 * 7. Referral code input field
 * 8. Self-referral error message
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CourseCard } from './CourseCard';

describe('CourseCard - Checkout Flow', () => {
  it.todo('shows "Locked" button for course without entitlement');

  it.todo('shows "Access Now" button for course with entitlement');

  it.todo('displays student price for student employment status');

  it.todo('displays employed price for employed employment status');

  it.todo('shows loading state when checkout button clicked');

  it.todo('handles API error gracefully with error message');

  it.todo('prevents self-referral with error message');

  it.todo('allows optional referral code (empty is valid)');
});

/**
 * Example Implementation (for reference):
 *
 * it('shows "Locked" button for course without entitlement', async () => {
 *   const course = {
 *     id: 1,
 *     title: 'Test Course',
 *     category: 'alacarte',
 *     hasAccess: false,
 *     price: 9.00,
 *   };
 *
 *   render(<CourseCard course={course} />);
 *
 *   const button = screen.getByRole('button', { name: /locked/i });
 *   expect(button).toBeDisabled();
 * });
 *
 * it('handles checkout API error gracefully', async () => {
 *   const course = { ... };
 *
 *   // Mock API call to fail
 *   vi.mock('@/lib/api/client', () => ({
 *     createCheckoutSession: vi.fn().mockRejectedValue(new Error('Network error'))
 *   }));
 *
 *   render(<CourseCard course={course} />);
 *
 *   const unlockButton = screen.getByRole('button', { name: /unlock/i });
 *   await userEvent.click(unlockButton);
 *
 *   await waitFor(() => {
 *     expect(screen.getByText(/unable to create checkout/i)).toBeInTheDocument();
 *   });
 * });
 */
```

**Also update `package.json`** to include test script if not present:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

**Acceptance Criteria**:
- Placeholder test file created with 8 TODO tests
- File includes example implementations in comments
- package.json includes test scripts

**Testing**:
- Verify file was created
- Run `npm test` to verify Vitest can discover the file (tests will show as TODO)

**Evidence Required**:
- File path: `/app/client/src/components/courses/CourseCard.test.tsx`
- Confirmation file exists and contains 8 TODO tests
- Output of `npm test` showing TODO tests

---

### Item 12: Add Already-Purchased Negative Test Case to E2E Markdown

**Issue**: E2E test doesn't cover what happens when a user tries to purchase a course they already own. Should the UI prevent this, or should the backend handle it?

**Why Low Priority**: Edge case that's unlikely in normal usage. More of a UX concern than functional bug.

**File to Modify**: `/.claude/commands/e2e/test_stripe_checkout.md`

**Implementation**:

Add this new edge case after "Edge Case 7: Network Failure During Checkout Initiation" (around line 220):

```markdown
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
```

**Acceptance Criteria**:
- New edge case added to E2E test markdown
- Includes 3 scenarios: UI prevention, backend prevention, gifting
- Includes implementation decision checklist
- Includes test steps and success criteria

**Testing**:
- Read file to verify edge case was added
- Verify markdown formatting is correct

**Evidence Required**:
- File path: `/.claude/commands/e2e/test_stripe_checkout.md`
- Line numbers where edge case was added
- Confirmation all 3 scenarios are present

---

### Item 13: Add Conditional Docs Triggers for Referrals/Refunds

**Issue**: The conditional_docs.md file doesn't include triggers for reading STRIPE_TESTING.md when working on referral system or refund handling.

**Why Low Priority**: Developers will likely read STRIPE_TESTING.md anyway when working on payments, but explicit triggers are better.

**File to Modify**: `/.claude/commands/conditional_docs.md`

**Implementation**:

Update the existing STRIPE_TESTING.md conditions (around line 125-140) to add 4 new triggers:

```markdown
- app_docs/testing/STRIPE_TESTING.md
  - Conditions:
    - When testing Stripe payment integration end-to-end
    - When setting up Stripe test mode vs live mode
    - When testing employment-based pricing logic
    - When testing course access control (free, alacarte, curriculum)
    - When using Stripe CLI for local webhook testing
    - When debugging checkout session creation
    - When verifying payment_intent metadata flow
    - When testing with Stripe test cards
    - When troubleshooting "course remains locked after payment"
    - When verifying price selection based on employment status
    - When testing alacarte per-course vs curriculum bundle access
    - When running create_test_products.py script
    - When switching between test and live mode
    - When performing manual or E2E Stripe testing
    - When implementing or testing referral system with Stripe payments  # NEW
    - When handling refunded payments or revoked entitlements  # NEW
    - When configuring product metadata in Stripe dashboard  # NEW
    - When diagnosing "No price available" errors  # NEW
    - When working with stripe_service.py or webhook signature verification  # NEW
    - When deploying Stripe integration to production  # NEW
```

**Acceptance Criteria**:
- 6 new conditions added to existing STRIPE_TESTING.md entry
- Conditions marked with `# NEW` comment for clarity
- No other changes to conditional_docs.md

**Testing**:
- Read file to verify conditions were added
- Count total conditions (should be 20 now)

**Evidence Required**:
- File path: `/.claude/commands/conditional_docs.md`
- Line numbers where conditions were added
- Confirmation 6 new conditions are present

---

## ✅ COMPLETION SUMMARY

After completing all 13 items, provide a summary with:

1. **Files Modified** (list with line number ranges)
2. **Tests Added** (count and file paths)
3. **Test Results** (all tests passing?)
4. **Documentation Sections** (count of new sections added)
5. **Verification** (evidence for each high-priority item)

## 📌 IMPORTANT REMINDERS

- **Run tests after EACH code change** - don't batch testing at the end
- **Mark todos complete immediately** - provide specific evidence
- **If blocked** - document why and continue to next item
- **Evidence is required** - file paths, line numbers, test output
- **No skipping** - execute all 13 items in order

---

**Good luck! 🚀**
