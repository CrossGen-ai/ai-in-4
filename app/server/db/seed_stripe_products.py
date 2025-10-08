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

        # Create products
        products_data = [
            {
                "id": "prod_free_intro",
                "name": "Free AI Intro Course",
                "description": "Introduction to AI fundamentals - completely free",
                "category": "free",
                "active": True,
            },
            {
                "id": "prod_ai_4_weekends",
                "name": "AI in 4 Weekends - Full Curriculum",
                "description": "Complete AI mastery program covering all fundamentals and advanced topics",
                "category": "curriculum",
                "active": True,
            },
            {
                "id": "prod_prompt_engineering",
                "name": "Prompt Engineering Mastery",
                "description": "Deep dive into advanced prompt engineering techniques",
                "category": "alacarte",
                "active": True,
            },
            {
                "id": "prod_ai_automation",
                "name": "AI Automation for Business",
                "description": "Learn how to automate business processes with AI tools",
                "category": "alacarte",
                "active": True,
            },
        ]

        prices_data = [
            # Free course has no price
            {
                "id": "price_ai_4_weekends",
                "product_id": "prod_ai_4_weekends",
                "amount": 29900,  # $299.00
                "currency": "usd",
                "active": True,
            },
            {
                "id": "price_prompt_engineering",
                "product_id": "prod_prompt_engineering",
                "amount": 9900,  # $99.00
                "currency": "usd",
                "active": True,
            },
            {
                "id": "price_ai_automation",
                "product_id": "prod_ai_automation",
                "amount": 14900,  # $149.00
                "currency": "usd",
                "active": True,
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
        print(f"✅ Seeded {len(products_data)} products and {len(prices_data)} prices")


if __name__ == "__main__":
    asyncio.run(seed_products())
