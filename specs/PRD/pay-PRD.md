## PRD: CrossGen AI Course Dashboard & Paywall System

### 1. Purpose

Create a unified **course dashboard** experience that dynamically displays courses and modules—some **free**, some **locked behind payment**—based on a logged-in user’s entitlements pulled from Stripe via the MCP server.

NOTES:  you have a stripe MCP server availbale to setup what you need when coding.
---

### 2. Core User Flow

**Step 1: Landing Page → Magic Link Login**

**Step 2: Dashboard View (Post-Login)**

* Display course **cards** grouped by category:

  1. **Free/Introductory Modules** – visible and fully clickable.
  2. **Curriculum Modules (4-Week Program)** – visible but locked with a paywall overlay.
  3. **A-La-Carte Courses** – visible with price and “Unlock” button (Stripe checkout).

* User sees a “Welcome Back” header, progress stats, and upcoming session reminders (if enrolled).

**Step 3: Unlocking Access**

* Clicking a locked card triggers the **Stripe MCP payment flow**:

  * Call `stripe.createCheckoutSession()` via MCP with parameters:

    * `product_id` (from Stripe Dashboard)
    * `user_email` (from auth session)
  * Upon success, redirect user to `Stripe Checkout` in a new tab.
  * Webhook/MCP callback `payment.success` updates local DB or user state to mark course as purchased.

**Step 4: Post-Purchase Access**

* Return user to `/dashboard`.
* Purchased card now unlocked with a “Resume Course” button.
* User gains access to course detail page `/course/:id`, which contains module list, progress, and videos/docs.

---

### 3. Course Card System

Each card has metadata in database or JSON schema:

```json
{
  "id": "course_4week_intro",
  "title": "AI in 4 Weekends",
  "description": "Live, interactive 4-week cohort to master AI tools and habits.",
  "type": "curriculum",
  "status": "locked",
  "price_id": "price_abc123",
  "thumbnail_url": "/images/4week.png",
  "tags": ["cohort", "interactive", "beginner"],
  "access": {"free": false, "purchased": false}
}
```

Logic:

* `free: true` → clickable immediately.
* `free: false` + `purchased: false` → blurred overlay + “Unlock” CTA.
* `purchased: true` → direct navigation enabled.

---

### 4. Paywall Logic (Frontend)

* Implement conditional rendering:

  * If `course.free` → `<Link>` active.
  * If locked → `<div class="locked-overlay">Unlock Access</div>`.
  * If purchased → `<Link>` to `/course/:id`.
* On “Unlock Access,” trigger MCP → `stripe.createCheckoutSession(course.price_id)` → redirect to checkout URL.

---

### 5. MCP–Stripe Integration

Required endpoints:

| Action          | MCP Call                                                         | Description                                      |
| --------------- | ---------------------------------------------------------------- | ------------------------------------------------ |
| Get products    | `stripe.products.list()`                                         | Fetch all active courses and prices from Stripe. |
| Create checkout | `stripe.checkout.sessions.create({price_id, user_email})`        | Returns checkout URL.                            |
| Verify purchase | `stripe.customers.list({email})` + `stripe.subscriptions.list()` | Verify entitlements post-purchase.               |
| Webhook event   | `payment.success`                                                | Update user record or local database.            |

Entitlement flag stored locally:

```json
{"user_entitlements": {"price_abc123": true}}
```

---

### 6. Course Detail Page

* `/course/:id` loads only if entitlement = true.
* Include:

  * Course overview (static text or markdown)
  * Module list with locked/unlocked states
  * Optional free preview video (first module visible to all)
  * “Upgrade to full course” button if user has partial/free access

---

### 7. A-La-Carte Logic

* Each a-la-carte course functions identically to the core flow, but with unique Stripe price IDs.
* Display prices on cards (e.g., `$49 • Self-Paced`).
* Include optional “Bundle” CTA:

  * “Enroll in all modules and save 20%” → one checkout session with multiple price IDs.

---

### 8. Data Model Summary

**User Table**

| Field         | Type     | Notes                 |
| ------------- | -------- | --------------------- |
| id            | UUID     | from auth system      |
| email         | string   | unique                |
| name          | string   | optional              |
| entitlements  | JSON     | key = Stripe price_id |
| referral_code | string   | optional              |
| created_at    | datetime |                       |

**Course Table**

| Field         | Type   | Notes                        |
| ------------- | ------ | ---------------------------- |
| id            | string | matches Stripe product id    |
| title         | string |                              |
| description   | string |                              |
| price_id      | string | Stripe price ID              |
| category      | enum   | free / curriculum / alacarte |
| thumbnail_url | string |                              |
| order_index   | int    | display sorting              |

---

### 9. Free Mini-Module (Lead Magnet)

Create a module available to everyone:
**Title:** “Your First AI Habit: The Five-Minute Prompt Routine.”

* 1 short video
* 1 downloadable prompt guide (PDF)
* 1 “practice” area with input/output example

At module end:

> “Ready to go deeper? Unlock the full 4-Week Experience.”

This mini-module sits on the dashboard as the first clickable card.

---

### 10. Access Control Summary

| Course Type | Logged-In User | Purchased | Shown | Clickable | Stripe CTA |
| ----------- | -------------- | --------- | ----- | --------- | ---------- |
| Free        | ✅              | N/A       | ✅     | ✅         | ❌          |
| Curriculum  | ✅              | ❌         | ✅     | ❌         | ✅          |
| Curriculum  | ✅              | ✅         | ✅     | ✅         | ❌          |
| A-La-Carte  | ✅              | ❌         | ✅     | ❌         | ✅          |
| A-La-Carte  | ✅              | ✅         | ✅     | ✅         | ❌          |

---

### 11. Admin Controls

* Pricing managed only in Stripe Dashboard.
* Product sync runs automatically via MCP `stripe.products.list()` daily or on admin refresh.
* Admin UI can show which users own which courses (optional future feature).

---

### 12. Future Scalability

* Add referral tracking via Stripe coupon codes.
* Introduce cohorts with start dates in dashboard.
* Enable progress tracking (percentage complete).

---

### 13. Referral & Credit System

#### Objective

Enable users to refer others via email and earn **automated refunds or credits** toward curriculum courses. Referrals are validated by **email match** during the referred user’s checkout process, and the referring user receives a **refund or credit** after the referral’s payment clears.

#### Flow Overview

1. **Referral Code Generation**

   * When a user logs in for the first time, generate a unique referral code.
   * Store in `user.referral_code`.
   * Display referral link: `https://ai-in-4.crossgen-ai.com/ref/<referral_code>`.
2. **Referral Capture**

   * Landing via `/ref/<code>` pre-fills referrer info during sign-up.
   * Referral code stored in Stripe Checkout `metadata`.
3. **Validation & Reward Logic**

   * On `payment.success` webhook:

     * Validate referrer.
     * Prevent duplicates.
     * Apply **credit/refund** to referrer.
4. **Communication**

   * Postmark transactional email confirms referral credit to referrer.

#### Dashboard Integration

* **Referral card** shows total confirmed referrals, pending referrals, credits earned.
* **Dynamic pricing indicator** updates price shown for courses based on referral count.

#### Database Fields (Additions)

**User Table**

| Field               | Type   | Description                               |
| ------------------- | ------ | ----------------------------------------- |
| referral_code       | string | unique per user                           |
| referrals_confirmed | int    | number of paid referrals                  |
| referral_credits    | int    | total credit amount in USD                |
| referral_history    | JSON   | list of referred user emails + timestamps |

**Referral Table (new)**

| Field         | Type     | Description                    |
| ------------- | -------- | ------------------------------ |
| id            | UUID     |                                |
| referrer_id   | FK(User) | who referred                   |
| referee_email | string   | who was referred               |
| course_id     | string   | course purchased               |
| payment_id    | string   | Stripe payment ID              |
| status        | enum     | pending / confirmed / credited |
| created_at    | datetime |                                |

#### Stripe MCP Integration

| Action                        | MCP Call                                                                                           | Description                                    |
| ----------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Create checkout with referral | `stripe.checkout.sessions.create({price_id, user_email, metadata:{referrer_code,referrer_email}})` | Logs referrer info                             |
| Webhook handler               | `payment.success`                                                                                  | Matches referral_code, issues refund or coupon |
| Create coupon/refund          | `stripe.coupons.create()` or `stripe.refunds.create()`                                             | Executes referral reward                       |
| Query user metadata           | `stripe.customers.retrieve(email)`                                                                 | Confirms referrer identity                     |

#### UX Copy Examples

**Dashboard Card:**

> "Invite friends! Share your link below and earn 25% back for every confirmed referral."

**Checkout Reminder:**

> "Got a friend who told you about this? Enter their email so they get credit."

#### Security & Abuse Prevention

* Credits applied only after successful payment.
* Prevent self-referrals.
* Cap total credits per user.

#### Summary

* Referrals validated via email and automated in Stripe.
* Users receive credits/refunds based on confirmed referrals.
* Encourages viral growth while maintaining trust and transparency.
