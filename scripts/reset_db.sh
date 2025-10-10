#!/bin/bash

echo "Starting database reset..."

# Navigate to server directory (from project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../app/server" || exit 1

# Step 1: Initialize database (drop and recreate all tables)
echo "1/3 Initializing database (dropping and recreating tables)..."
uv run python db/init_db.py
if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to initialize database"
    exit 1
fi

# Step 2: Seed with sample data (users and courses)
echo "2/3 Seeding database with sample data..."
uv run python db/seed_db.py
if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to seed database"
    exit 1
fi

# Step 3: Seed Stripe products and prices
echo "3/3 Seeding Stripe products..."
uv run python db/seed_stripe_products.py
if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to seed Stripe products"
    exit 1
fi

echo "✓ Database reset successfully completed"