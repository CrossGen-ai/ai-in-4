# Stripe Payment Integration Testing Guide

Comprehensive guide for testing Stripe payment integration with employment-based pricing and course access control.

## Table of Contents

1. [Overview](#overview)
2. [Test Mode vs Live Mode](#test-mode-vs-live-mode)
3. [Environment Setup](#environment-setup)
4. [Employment-Based Pricing](#employment-based-pricing)
5. [Course Access Control Logic](#course-access-control-logic)
6. [Testing with Stripe CLI](#testing-with-stripe-cli)
7. [Test Cards](#test-cards)
8. [Unit Testing](#unit-testing)
9. [E2E Testing](#e2e-testing)
10. [Common Issues](#common-issues)

## Overview

The Stripe integration supports:
- **Employment-based pricing**: Automatically selects price tier based on user's employment status
- **Category-based access control**: Different access logic for free, alacarte, and curriculum courses
- **Webhook-driven entitlements**: Course access granted via `payment_intent.succeeded` webhook
- **Idempotent webhook handling**: Prevents duplicate entitlements from retry webhooks
- **Referral system**: 25% credit to referrer on successful purchase

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

## Test Mode vs Live Mode

Stripe provides two completely separate environments:

### Test Mode
- **API Keys**: Start with `sk_test_` and `pk_test_`
- **Payments**: No real money, use test cards
- **Webhooks**: Can be tested locally with Stripe CLI
- **Products/Prices**: Separate from live mode
- **Database**: Use same database with test mode product/price IDs

### Live Mode
- **API Keys**: Start with `sk_live_` and `pk_live_`
- **Payments**: Real money transactions
- **Webhooks**: Must be publicly accessible
- **Products/Prices**: Production data
- **Database**: Same database with live mode product/price IDs

### Switching Between Modes

1. **Update .env file**:
   ```bash
   # Test Mode
   STRIPE_SECRET_KEY=sk_test_51...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_TEST_MODE=true

   # Live Mode
   STRIPE_SECRET_KEY=sk_live_51...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_TEST_MODE=false
   ```

2. **Create test mode products**: Run `/app/server/create_test_products.py` to mirror live products in test mode

3. **Database considerations**: Products and prices use Stripe IDs as primary keys, so test and live mode products have different IDs

## Environment Setup

### Required Environment Variables

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_51Qxdof3wtYkejByQ...  # Backend API calls
STRIPE_PUBLISHABLE_KEY=pk_test_...               # Frontend checkout
STRIPE_WEBHOOK_SECRET=whsec_...                  # Webhook signature verification

# App URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

# Test Mode Flag
STRIPE_TEST_MODE=true
```

### Database Setup

Ensure database has test mode products/prices:

```bash
cd /app/server
uv run python create_test_products.py
```

This script:
- Creates products in Stripe test mode
- Updates database with test mode product/price IDs
- Configures employment-based pricing metadata

### Stripe CLI Installation

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Linux
wget https://github.com/stripe/stripe-cli/releases/download/vX.X.X/stripe_X.X.X_linux_x86_64.tar.gz
tar -xvf stripe_X.X.X_linux_x86_64.tar.gz

# Verify installation
stripe --version
```

### Stripe CLI Login

```bash
stripe login
# Follow browser prompt to authenticate
```

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

## Employment-Based Pricing

### Pricing Tiers

**Student/Reduced Rate**:
- Employment statuses: `Student`, `Between jobs`, `Homemaker`, `Retired`, `Other`
- Example pricing:
  - Alacarte courses: $9.00
  - Curriculum bundle: $97.00

**Employed Rate**:
- Employment statuses: `Employed full-time`, `Employed part-time`, `Self-employed/Freelancer`
- Example pricing:
  - Alacarte courses: $97.00
  - Curriculum bundle: $497.00

### Price Selection Logic

Located in `app/server/api/routes/payments.py:76-105`:

```python
# Get user's employment status from UserExperience table
employment_status = experience.employment_status

# Get all active prices for product
prices = await db.execute(
    select(StripePrice)
    .where(StripePrice.product_id == product_id)
    .where(StripePrice.active == True)
)

# Select price based on employment eligibility
for price in prices:
    if price.stripe_metadata and "eligible_employment_statuses" in price.stripe_metadata:
        eligible_statuses = price.stripe_metadata["eligible_employment_statuses"]
        if employment_status in eligible_statuses:
            selected_price = price
            break
```

### Testing Price Selection

**Test Case 1: Student User**
```python
# Set user employment status
user_experience.employment_status = "Student"
await db.commit()

# Create checkout session
response = client.post("/api/payments/checkout", json={"product_id": "prod_test_123"})

# Verify student price selected
assert response.status_code == 200
# Check Stripe mock to verify price_id matches student rate
```

**Test Case 2: Employed User**
```python
user_experience.employment_status = "Employed full-time"
await db.commit()

response = client.post("/api/payments/checkout", json={"product_id": "prod_test_123"})
# Verify employed price selected
```

**Test Case 3: Missing Employment Status**
```python
# Delete user experience
await db.delete(user_experience)
await db.commit()

response = client.post("/api/payments/checkout", json={"product_id": "prod_test_123"})
assert response.status_code == 400
assert "employment status not found" in response.json()["detail"]
```

## Course Access Control Logic

Located in `app/server/services/entitlement_service.py:147-194`

### Access Rules by Category

1. **free** (Category: `free`)
   - Always accessible
   - No payment required
   - No entitlement check

2. **alacarte** (Category: `alacarte`)
   - Per-course access
   - Must have entitlement to **specific** product
   - Buying one alacarte course does NOT grant access to other alacarte courses
   - Requires `course.stripe_product_id` to match purchased product

3. **curriculum** (Category: `curriculum`)
   - Bundle access
   - Any curriculum product purchase unlocks ALL curriculum courses
   - Checks for entitlement to ANY product with `category == "curriculum"`

4. **unique** (Category: `unique`)
   - Per-course access (same as alacarte)
   - Must have entitlement to specific product

### Testing Access Control

**Unit Test: Free Course**
```python
@pytest.mark.asyncio
async def test_check_course_access_free_course_always_accessible(test_db, test_user, free_course):
    has_access = await check_course_access(test_user.id, free_course, test_db)
    assert has_access is True
```

**Unit Test: Alacarte Per-Course Access**
```python
@pytest.mark.asyncio
async def test_check_course_access_alacarte_per_course_not_category(
    test_db, test_user, alacarte_course, second_alacarte_course, test_stripe_price
):
    # Grant entitlement for first course only
    await grant_entitlement(
        user_id=test_user.id,
        price_id=test_stripe_price.id,
        payment_intent_id="pi_test_123",
        db=test_db,
    )

    # Check access
    has_access_first = await check_course_access(test_user.id, alacarte_course, test_db)
    has_access_second = await check_course_access(test_user.id, second_alacarte_course, test_db)

    # Only first course should be accessible
    assert has_access_first is True
    assert has_access_second is False  # KEY ASSERTION
```

**Unit Test: Curriculum Bundle Access**
```python
@pytest.mark.asyncio
async def test_check_course_access_curriculum_bundle_access(
    test_db, test_user, curriculum_course, second_curriculum_course, curriculum_price
):
    # Grant entitlement to ONE curriculum product
    await grant_entitlement(
        user_id=test_user.id,
        price_id=curriculum_price.id,
        payment_intent_id="pi_test_456",
        db=test_db,
    )

    # Check access to BOTH curriculum courses
    has_access_first = await check_course_access(test_user.id, curriculum_course, test_db)
    has_access_second = await check_course_access(test_user.id, second_curriculum_course, test_db)

    # Both should be accessible (bundle logic)
    assert has_access_first is True
    assert has_access_second is True
```

## Testing with Stripe CLI

### Start Webhook Listener

```bash
# Terminal 1: Start webhook forwarding
cd /app/server
stripe listen --api-key sk_test_51... --forward-to http://localhost:8000/api/payments/webhook

# Copy webhook signing secret from output
# Ready! Your webhook signing secret is 'whsec_...' (^C to quit)
```

**Update .env with webhook secret**:
```bash
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Trigger Test Webhooks

**Method 1: Real Stripe Checkout**
```bash
# Complete checkout flow in browser
# Stripe CLI automatically forwards webhook events
```

**Method 2: Manual Webhook Trigger**
```bash
stripe trigger payment_intent.succeeded
```

**Method 3: Custom Event**
```bash
stripe trigger payment_intent.succeeded \
  --override payment_intent:metadata='{"user_id":"1","price_id":"price_test_123"}'
```

### Verify Webhook Processing

Check terminal output for:
```
2025-10-09 12:34:56   --> payment_intent.succeeded [200]
```

Check backend logs for:
```
INFO: Received webhook event: payment_intent.succeeded
INFO: Granted entitlement for user 1, price price_test_123
```

## Test Cards

Stripe provides test cards for various scenarios:

### Success
```
Card Number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/34)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

### Declined
```
Card Number: 4000 0000 0000 0002
Result: Generic decline
```

### Insufficient Funds
```
Card Number: 4000 0000 0000 9995
Result: Card declined due to insufficient funds
```

### 3D Secure Required
```
Card Number: 4000 0025 0000 3155
Result: Requires authentication
```

### All Test Cards
https://stripe.com/docs/testing#cards

## Unit Testing

### Test File Structure

```
/app/server/tests/
├── test_payments.py              # Payment routes and checkout
├── test_entitlement_service.py   # Access control logic
└── conftest.py                   # Shared fixtures
```

### Key Test Coverage

**Checkout Session Creation**
- Employment-based price selection
- Metadata passed to payment_intent
- Referrer code validation
- Error handling (missing employment status, invalid product)

**Webhook Processing**
- Entitlement grant on `payment_intent.succeeded`
- Idempotency (duplicate webhook handling)
- Referral credit application
- Error handling (missing metadata, database errors)

**Access Control**
- Free course always accessible
- Alacarte per-course access
- Curriculum bundle access
- Missing product_id handling

### Running Tests

```bash
# All payment tests
cd /app/server
uv run pytest tests/test_payments.py -v

# Specific test
uv run pytest tests/test_payments.py::test_checkout_creates_session_with_valid_auth -v

# All entitlement tests
uv run pytest tests/test_entitlement_service.py -v

# With coverage
uv run pytest tests/ --cov=api --cov=services --cov-report=html
```

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

## E2E Testing

### E2E Test Flow

See `.claude/commands/e2e/test_stripe_checkout.md` for complete E2E test specification.

**High-Level Steps**:
1. Login as test user with employment status set
2. Navigate to dashboard
3. Identify locked course
4. Click "Unlock Access"
5. Verify correct price displayed on Stripe checkout (based on employment status)
6. Complete payment with test card (4242 4242 4242 4242)
7. Wait for webhook processing
8. Verify course unlocked (button changes to "Access Now")
9. Verify course content accessible
10. Verify entitlement persists across sessions

### Playwright E2E Test

```bash
cd /app/client
npx playwright test test_stripe_checkout.spec.ts
```

### Manual E2E Testing

1. **Setup**:
   ```bash
   # Terminal 1: Backend
   cd /app/server
   uv run uvicorn main:app --reload

   # Terminal 2: Frontend
   cd /app/client
   npm run dev

   # Terminal 3: Stripe webhooks
   stripe listen --forward-to http://localhost:8000/api/payments/webhook
   ```

2. **Test Flow**:
   - Login: http://localhost:5173/dev-login
   - Complete profile with employment status
   - Dashboard: Find locked course
   - Click "Unlock Access"
   - Stripe checkout: Use `4242 4242 4242 4242`
   - Verify redirect to dashboard
   - Verify course now shows "Access Now"
   - Click course to verify content accessible

## Common Issues

### Issue 1: Course Remains Locked After Payment

**Symptoms**: Payment succeeds but course still shows "Locked"

**Debugging**:
1. Check Stripe CLI output for webhook delivery:
   ```
   --> payment_intent.succeeded [200]
   ```
2. Check backend logs for entitlement grant:
   ```
   INFO: Granted entitlement for user X, price price_Y
   ```
3. Query database:
   ```sql
   SELECT * FROM entitlements WHERE user_id = X;
   ```
4. Check frontend refetch after redirect

**Common Causes**:
- Webhook not reaching backend (firewall, network issue)
- Metadata not passed in `payment_intent_data`
- Database transaction not committed
- Frontend not refetching entitlements after redirect

**Fix**: Ensure `payment_intent_data` includes metadata (see `payments.py:150-152`)

### Issue 2: Wrong Price Selected

**Symptoms**: Employed user sees student rate or vice versa

**Debugging**:
1. Check user's employment status:
   ```sql
   SELECT employment_status FROM user_experience WHERE user_id = X;
   ```
2. Check price metadata:
   ```sql
   SELECT id, amount, stripe_metadata FROM stripe_prices WHERE product_id = 'prod_...';
   ```
3. Check backend logs for price selection logic

**Common Causes**:
- User's `employment_status` is NULL or not set
- Price metadata doesn't include `eligible_employment_statuses`
- Employment status spelling mismatch

**Fix**: Ensure user completes profile and metadata is correctly set on prices

### Issue 3: Alacarte Course Grants Access to All Alacarte Courses

**Symptoms**: Buying one alacarte course unlocks all alacarte courses

**Debugging**:
1. Check course `stripe_product_id`:
   ```sql
   SELECT id, title, category, stripe_product_id FROM courses WHERE category = 'alacarte';
   ```
2. Check access control logic in `entitlement_service.py:171-176`

**Common Causes**:
- Course `stripe_product_id` is NULL
- Access logic incorrectly checking category instead of specific product

**Fix**:
- Update courses table to set `stripe_product_id`
- Verify `check_course_access()` uses `check_product_access()` for alacarte

### Issue 4: Webhook Signature Verification Fails

**Symptoms**: Webhook returns 400 with "Invalid signature"

**Debugging**:
1. Check `STRIPE_WEBHOOK_SECRET` in .env
2. Compare with Stripe CLI output or Stripe dashboard webhook secret
3. Verify raw body is used for signature verification (not parsed JSON)

**Common Causes**:
- Wrong webhook secret in .env
- Request body already parsed before signature verification

**Fix**: Update .env with correct webhook secret from Stripe CLI or dashboard

### Issue 5: Test Mode vs Live Mode ID Mismatch

**Symptoms**: 404 errors for products/prices, or live charges in test mode

**Debugging**:
1. Check API key prefix in .env:
   - Test: `sk_test_...`
   - Live: `sk_live_...`
2. Check product IDs in database vs Stripe dashboard

**Common Causes**:
- Database has live mode IDs but .env has test mode keys
- Forgot to run `create_test_products.py` after switching to test mode

**Fix**: Run `create_test_products.py` to sync test mode products to database

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

## Best Practices

1. **Always test in test mode first**: Never test checkout flow with live API keys
2. **Use Stripe CLI for local webhook testing**: More reliable than ngrok/localtunnel
3. **Verify metadata flow**: Check that user_id, price_id flow from checkout → payment_intent → webhook
4. **Test all employment statuses**: Ensure pricing works for all 8 employment status values
5. **Test access control edge cases**: Especially alacarte per-course vs curriculum bundle logic
6. **Verify idempotency**: Test that duplicate webhooks don't create duplicate entitlements
7. **Check database state**: Don't rely solely on UI; query database to verify entitlements created
8. **Monitor webhook logs**: Watch Stripe CLI output to catch webhook delivery issues early

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

## Related Documentation

- [E2E Test Specification](.claude/commands/e2e/test_stripe_checkout.md)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Test Mode Guide](https://stripe.com/docs/test-mode)
- [Stripe CLI Reference](https://stripe.com/docs/stripe-cli)
