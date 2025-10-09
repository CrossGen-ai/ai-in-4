#!/bin/bash
# Check if Stripe CLI webhook listener is running for payment integration tests

set -e

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI not installed"
    echo "Install with: brew install stripe/stripe-cli/stripe"
    exit 1
fi

# Check if stripe listen is running
if ps aux | grep "stripe listen" | grep -v grep > /dev/null; then
    echo "✅ Stripe CLI webhook listener is running"

    # Show the forwarding URL
    FORWARD_URL=$(ps aux | grep "stripe listen" | grep -v grep | grep -o "http://[^ ]*")
    echo "   Forwarding to: $FORWARD_URL"

    exit 0
else
    echo "⚠️  Stripe CLI webhook listener is NOT running"
    echo ""
    echo "Webhook tests require Stripe CLI to be running."
    echo "Start it with:"
    echo ""
    echo "  stripe listen --api-key \$STRIPE_SECRET_KEY --forward-to http://localhost:8000/api/payments/webhook"
    echo ""
    echo "Or if you're only running unit tests (mocked), you can ignore this warning."

    exit 1
fi
