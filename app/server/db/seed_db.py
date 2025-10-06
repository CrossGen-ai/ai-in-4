"""Seed the database with sample data for development."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import AsyncSessionLocal
from db.models import User, UserExperience, Course


async def seed_db():
    """Seed database with sample users and courses."""
    async with AsyncSessionLocal() as db:
        # Create sample users
        users_data = [
            {
                "email": "john@example.com",
                "experience_level": "Beginner",
                "background": "Marketing professional interested in AI",
                "goals": "Learn how to use AI tools in my daily work"
            },
            {
                "email": "sarah@example.com",
                "experience_level": "Intermediate",
                "background": "Software developer with some ML experience",
                "goals": "Build AI-powered applications"
            },
            {
                "email": "mike@example.com",
                "experience_level": "Advanced",
                "background": "Data scientist with AI research background",
                "goals": "Stay current with latest AI developments"
            }
        ]

        for user_data in users_data:
            # Create user
            user = User(
                email=user_data["email"],
                is_active=True
            )
            db.add(user)
            await db.flush()

            # Create experience profile
            experience = UserExperience(
                user_id=user.id,
                experience_level=user_data["experience_level"],
                background=user_data["background"],
                goals=user_data["goals"]
            )
            db.add(experience)

        # Create sample courses
        courses_data = [
            {
                "title": "AI Fundamentals: Understanding the Basics",
                "description": "Learn the core concepts of artificial intelligence and machine learning",
                "schedule": "Every Monday, 6:00 PM - 8:00 PM PST",
                "materials_url": "https://example.com/ai-fundamentals"
            },
            {
                "title": "Practical AI: Building Real Applications",
                "description": "Hands-on course on building AI-powered applications",
                "schedule": "Every Wednesday, 6:00 PM - 8:00 PM PST",
                "materials_url": "https://example.com/practical-ai"
            },
            {
                "title": "Advanced AI: LLMs and Beyond",
                "description": "Deep dive into large language models and cutting-edge AI",
                "schedule": "Every Friday, 6:00 PM - 8:00 PM PST",
                "materials_url": "https://example.com/advanced-ai"
            }
        ]

        for course_data in courses_data:
            course = Course(**course_data)
            db.add(course)

        await db.commit()
        print("Database seeded successfully!")
        print(f"Created {len(users_data)} users and {len(courses_data)} courses")


if __name__ == "__main__":
    asyncio.run(seed_db())
