#!/bin/bash
# Run payment tests with appropriate checks
# Usage: ./scripts/test_payments.sh [unit|integration|all]

set -e

cd "$(dirname "$0")/.."

TEST_TYPE="${1:-all}"

echo "🧪 Payment Test Runner"
echo "======================"

case $TEST_TYPE in
  unit)
    echo "Running unit tests (mocked, no Stripe CLI needed)..."
    cd app/server
    uv run pytest tests/test_payments.py -v
    ;;

  integration)
    echo "Running integration tests (requires Stripe CLI)..."
    echo ""

    # Check if Stripe CLI is running
    if ! ./scripts/check_stripe_cli.sh; then
      echo ""
      echo "Cannot run integration tests without Stripe CLI."
      echo "Either:"
      echo "  1. Start Stripe CLI and try again"
      echo "  2. Run unit tests only: ./scripts/test_payments.sh unit"
      exit 1
    fi

    echo ""
    cd app/server
    uv run pytest tests/test_payment_integration.py -v
    ;;

  all)
    echo "Running all payment tests..."
    echo ""

    # Run unit tests (always work)
    echo "📦 Unit Tests (mocked)"
    cd app/server
    uv run pytest tests/test_payments.py -v

    echo ""
    echo "🌐 Integration Tests (webhook)"

    # Check for Stripe CLI
    if ./scripts/check_stripe_cli.sh; then
      echo ""
      uv run pytest tests/test_payment_integration.py -v
    else
      echo ""
      echo "⚠️  Skipping integration tests (Stripe CLI not running)"
      echo "   Unit tests passed. Run integration tests separately when ready."
      exit 0
    fi
    ;;

  *)
    echo "❌ Invalid test type: $TEST_TYPE"
    echo "Usage: ./scripts/test_payments.sh [unit|integration|all]"
    exit 1
    ;;
esac

echo ""
echo "✅ Payment tests completed successfully"
