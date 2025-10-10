#!/usr/bin/env python3
"""
Create test mode Stripe products and prices that mirror live mode setup.
This script creates products/prices in Stripe test mode and updates the database.
"""
import stripe
import json
from sqlalchemy import create_engine, text
from core.config import settings

# Initialize Stripe with test key
stripe.api_key = settings.STRIPE_SECRET_KEY
print(f"Using Stripe API key: {stripe.api_key[:12]}...")
print(f"Test mode: {settings.STRIPE_TEST_MODE}")

# Connect to database
engine = create_engine('sqlite:///./db/database.db')

# Product definitions
products_to_create = [
    {
        "name": "Free AI Intro Course",
        "description": "Introduction to AI fundamentals - completely free",
        "category": "free",
        "prices": []  # No prices for free course
    },
    {
        "name": "AI in 4 Weekends - Full Curriculum",
        "description": "Complete AI mastery program covering all fundamentals and advanced topics",
        "category": "curriculum",
        "prices": [
            {
                "amount": 9700,  # $97.00
                "currency": "usd",
                "metadata": {
                    "price_name": "AI in 4 Weekends - Student/Reduced Rate",
                    "eligible_employment_statuses": ["Student", "Between jobs", "Homemaker", "Retired", "Other"]
                }
            },
            {
                "amount": 49700,  # $497.00
                "currency": "usd",
                "metadata": {
                    "price_name": "AI in 4 Weekends - Employed Rate",
                    "eligible_employment_statuses": ["Employed full-time", "Employed part-time", "Self-employed/Freelancer"]
                }
            }
        ]
    },
    {
        "name": "Prompt Engineering Mastery",
        "description": "Deep dive into advanced prompt engineering techniques",
        "category": "alacarte",
        "prices": [
            {
                "amount": 900,  # $9.00
                "currency": "usd",
                "metadata": {
                    "price_name": "Prompt Engineering - Student/Reduced Rate",
                    "eligible_employment_statuses": ["Student", "Between jobs", "Homemaker", "Retired", "Other"]
                }
            },
            {
                "amount": 9700,  # $97.00
                "currency": "usd",
                "metadata": {
                    "price_name": "Prompt Engineering - Employed Rate",
                    "eligible_employment_statuses": ["Employed full-time", "Employed part-time", "Self-employed/Freelancer"]
                }
            }
        ]
    },
    {
        "name": "AI Automation for Business",
        "description": "Learn how to automate business processes with AI tools",
        "category": "alacarte",
        "prices": [
            {
                "amount": 4900,  # $49.00
                "currency": "usd",
                "metadata": {
                    "price_name": "AI Automation - Student/Reduced Rate",
                    "eligible_employment_statuses": ["Student", "Between jobs", "Homemaker", "Retired", "Other"]
                }
            },
            {
                "amount": 19700,  # $197.00
                "currency": "usd",
                "metadata": {
                    "price_name": "AI Automation - Employed Rate",
                    "eligible_employment_statuses": ["Employed full-time", "Employed part-time", "Self-employed/Freelancer"]
                }
            }
        ]
    }
]

print("\n" + "="*60)
print("Creating Test Mode Products and Prices")
print("="*60)

mapping = {}

with engine.connect() as conn:
    for product_def in products_to_create:
        print(f"\n📦 Creating product: {product_def['name']}")

        # Create product in Stripe
        stripe_product = stripe.Product.create(
            name=product_def['name'],
            description=product_def['description'],
        )

        product_id = stripe_product.id
        print(f"   ✅ Created: {product_id}")

        # Get old product ID from database
        result = conn.execute(
            text("SELECT id FROM stripe_products WHERE name = :name AND category = :cat"),
            {"name": product_def['name'], "cat": product_def['category']}
        )
        old_row = result.fetchone()
        old_product_id = old_row[0] if old_row else None

        # Update product in database
        if old_product_id:
            conn.execute(
                text("UPDATE stripe_products SET id = :new_id WHERE id = :old_id"),
                {"new_id": product_id, "old_id": old_product_id}
            )
            conn.commit()
            print(f"   📝 Updated database: {old_product_id} → {product_id}")
            mapping[old_product_id] = product_id

        # Create prices
        for price_def in product_def['prices']:
            print(f"   💰 Creating price: ${price_def['amount']/100:.2f}")

            # Convert metadata to strings (Stripe requirement)
            stripe_metadata = {}
            for key, value in price_def['metadata'].items():
                if isinstance(value, (list, dict)):
                    stripe_metadata[key] = json.dumps(value)
                else:
                    stripe_metadata[key] = str(value)

            stripe_price = stripe.Price.create(
                product=product_id,
                unit_amount=price_def['amount'],
                currency=price_def['currency'],
                metadata=stripe_metadata
            )

            price_id = stripe_price.id
            print(f"      ✅ Created: {price_id}")
            print(f"      Eligible: {price_def['metadata']['eligible_employment_statuses']}")

            # Insert price into database
            conn.execute(
                text("""INSERT INTO stripe_prices
                        (id, product_id, amount, currency, active, stripe_metadata, updated_at)
                        VALUES (:id, :product_id, :amount, :currency, 1, :metadata, CURRENT_TIMESTAMP)"""),
                {
                    "id": price_id,
                    "product_id": product_id,
                    "amount": price_def['amount'],
                    "currency": price_def['currency'],
                    "metadata": json.dumps(price_def['metadata'])
                }
            )
            conn.commit()
            print("      📝 Added to database")

print("\n" + "="*60)
print("✅ Test Mode Setup Complete!")
print("="*60)
print("\nProduct ID Mapping:")
for old_id, new_id in mapping.items():
    print(f"  {old_id} → {new_id}")
print("\n🎉 Ready to test Stripe checkout!")
