"""Seed database with Stripe products and prices."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import AsyncSessionLocal
from db.models import StripeProduct, StripePrice
from sqlalchemy import select


async def seed_products():
    """Seed test products and prices."""
    async with AsyncSessionLocal() as db:
        # Check if products already exist
        result = await db.execute(select(StripeProduct))
        existing = result.scalars().all()

        if existing:
            print(f"Found {len(existing)} existing products. Skipping seed.")
            return

        # Create products (using actual Stripe product IDs)
        products_data = [
            {
                "id": "prod_TCAigUbDPx6MT5",  # Real Stripe ID
                "name": "Free AI Intro Course",
                "description": "Introduction to AI fundamentals - completely free",
                "category": "free",
                "active": True,
            },
            {
                "id": "prod_TCAioeHdUlGMVO",  # Real Stripe ID
                "name": "AI in 4 Weekends - Full Curriculum",
                "description": "Complete AI mastery program covering all fundamentals and advanced topics",
                "category": "curriculum",
                "active": True,
            },
            {
                "id": "prod_TCAiojfK01AwZx",  # Real Stripe ID
                "name": "Prompt Engineering Mastery",
                "description": "Deep dive into advanced prompt engineering techniques",
                "category": "alacarte",
                "active": True,
            },
            {
                "id": "prod_TCAi4oXFhXL7OG",  # Real Stripe ID
                "name": "AI Automation for Business",
                "description": "Learn how to automate business processes with AI tools",
                "category": "alacarte",
                "active": True,
            },
        ]

        # Prices with employment-based eligibility (using actual Stripe price IDs)
        prices_data = [
            # AI in 4 Weekends - Full Curriculum
            {
                "id": "price_1SG7jC3wtYkejByQPKYaAAD4",  # Real Stripe ID
                "product_id": "prod_TCAioeHdUlGMVO",
                "amount": 49700,  # $497.00
                "currency": "usd",
                "active": True,
                "stripe_metadata": {
                    "price_name": "AI in 4 Weekends - Employed Rate",
                    "eligible_employment_statuses": [
                        "Employed full-time",
                        "Employed part-time",
                        "Self-employed/Freelancer"
                    ]
                }
            },
            {
                "id": "price_1SG7jK3wtYkejByQwpHzEjF1",  # Real Stripe ID
                "product_id": "prod_TCAioeHdUlGMVO",
                "amount": 9700,  # $97.00
                "currency": "usd",
                "active": True,
                "stripe_metadata": {
                    "price_name": "AI in 4 Weekends - Student/Reduced Rate",
                    "eligible_employment_statuses": [
                        "Student",
                        "Between jobs",
                        "Homemaker",
                        "Retired",
                        "Other"
                    ]
                }
            },

            # Prompt Engineering Mastery
            {
                "id": "price_1SG7jU3wtYkejByQmR5uoVKq",  # Real Stripe ID
                "product_id": "prod_TCAiojfK01AwZx",
                "amount": 9700,  # $97.00
                "currency": "usd",
                "active": True,
                "stripe_metadata": {
                    "price_name": "Prompt Engineering - Employed Rate",
                    "eligible_employment_statuses": [
                        "Employed full-time",
                        "Employed part-time",
                        "Self-employed/Freelancer"
                    ]
                }
            },
            {
                "id": "price_1SG7je3wtYkejByQWuEc85M6",  # Real Stripe ID
                "product_id": "prod_TCAiojfK01AwZx",
                "amount": 900,  # $9.00
                "currency": "usd",
                "active": True,
                "stripe_metadata": {
                    "price_name": "Prompt Engineering - Student/Reduced Rate",
                    "eligible_employment_statuses": [
                        "Student",
                        "Between jobs",
                        "Homemaker",
                        "Retired",
                        "Other"
                    ]
                }
            },

            # AI Automation for Business
            {
                "id": "price_1SG7jk3wtYkejByQyG8DbhWM",  # Real Stripe ID
                "product_id": "prod_TCAi4oXFhXL7OG",
                "amount": 19700,  # $197.00
                "currency": "usd",
                "active": True,
                "stripe_metadata": {
                    "price_name": "AI Automation - Employed Rate",
                    "eligible_employment_statuses": [
                        "Employed full-time",
                        "Employed part-time",
                        "Self-employed/Freelancer"
                    ]
                }
            },
            {
                "id": "price_1SG7jr3wtYkejByQ03ztlbQy",  # Real Stripe ID
                "product_id": "prod_TCAi4oXFhXL7OG",
                "amount": 4900,  # $49.00
                "currency": "usd",
                "active": True,
                "stripe_metadata": {
                    "price_name": "AI Automation - Student/Reduced Rate",
                    "eligible_employment_statuses": [
                        "Student",
                        "Between jobs",
                        "Homemaker",
                        "Retired",
                        "Other"
                    ]
                }
            },
        ]

        # Add products
        for product_data in products_data:
            product = StripeProduct(**product_data)
            db.add(product)

        # Add prices
        for price_data in prices_data:
            price = StripePrice(**price_data)
            db.add(price)

        await db.commit()
        print(f"✅ Seeded {len(products_data)} products and {len(prices_data)} prices with employment-based eligibility")


if __name__ == "__main__":
    asyncio.run(seed_products())
