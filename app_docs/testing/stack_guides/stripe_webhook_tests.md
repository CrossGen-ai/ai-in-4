# Stripe Webhook Testing Guide

## Overview

Stripe webhook tests require the **Stripe CLI** to be running locally to forward webhook events to your development server. This is **only needed for webhook-related payment tests**, not for checkout or price selection tests.

## When You Need This

**Required for:**
- Testing webhook event handlers (`/api/payments/webhook`)
- Testing payment intent success flows
- Testing entitlement granting after payment
- Testing referral credit application
- Any test that simulates Stripe sending webhook events

**Not required for:**
- Testing checkout session creation
- Testing price selection logic
- Testing product/price validation
- Unit tests that mock Stripe responses

## Setup for Webhook Testing

### 1. Install Stripe CLI (One-time setup)

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Other platforms: https://stripe.com/docs/stripe-cli
```

### 2. Start Webhook Forwarding

**Before running webhook tests**, start the Stripe CLI listener:

```bash
stripe listen \
  --api-key $STRIPE_SECRET_KEY \
  --forward-to http://localhost:8000/api/payments/webhook
```

**What this does:**
- Listens for Stripe test events
- Forwards them to your local `/api/payments/webhook` endpoint
- Provides a webhook signing secret (starts with `whsec_...`)

### 3. Update .env with Webhook Secret

The Stripe CLI outputs a webhook secret when it starts. Add it to your `.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Running Tests

### Option 1: Run All Payment Tests (Requires Stripe CLI)

```bash
# Start Stripe CLI in one terminal
stripe listen --api-key $STRIPE_SECRET_KEY --forward-to http://localhost:8000/api/payments/webhook

# Run tests in another terminal
uv run pytest tests/test_payment_integration.py -v
```

### Option 2: Run Only Non-Webhook Tests (No Stripe CLI needed)

```bash
# These tests mock Stripe and don't need the CLI
uv run pytest tests/test_payments.py -v
```

## Test Categories

### Unit Tests (No Stripe CLI)
- `test_payments.py` - Mocked Stripe checkout tests
- `test_checkout_creates_session_with_valid_auth`
- `test_checkout_selects_price_based_on_employment_status`

### Integration Tests (Requires Stripe CLI)
- `test_payment_integration.py` - Real webhook event tests
- `test_webhook_handles_payment_intent_succeeded`
- `test_webhook_grants_entitlements`
- `test_webhook_processes_referrals`

## Troubleshooting

### "Webhook signature verification failed"
**Cause:** Stripe CLI not running or wrong webhook secret in `.env`

**Fix:**
1. Ensure Stripe CLI is running: `ps aux | grep "stripe listen"`
2. Copy the `whsec_...` secret from CLI output to `.env`
3. Restart your FastAPI server to reload environment

### "Connection refused" on webhook
**Cause:** FastAPI server not running on port 8000

**Fix:**
```bash
# Start server in one terminal
uv run uvicorn main:app --reload --port 8000

# Start Stripe CLI in another
stripe listen --api-key $STRIPE_SECRET_KEY --forward-to http://localhost:8000/api/payments/webhook
```

### Tests timeout waiting for webhook
**Cause:** Webhook event not forwarded

**Fix:**
1. Check Stripe CLI shows "Ready!" message
2. Verify webhook URL matches your server: `http://localhost:8000/api/payments/webhook`
3. Check server logs for incoming POST requests

## Quick Validation Script

Check if Stripe CLI is running:

```bash
# Returns process if running, empty if not
ps aux | grep "stripe listen" | grep -v grep
```

Expected output when running:
```
user  12345  stripe listen --api-key sk_test_... --forward-to http://localhost:8000/api/payments/webhook
```

## Production Note

**Stripe CLI is only for local development.**

In production:
- Configure webhook endpoints in Stripe Dashboard
- Use static webhook secrets from Dashboard
- Stripe sends events directly to your deployed server
