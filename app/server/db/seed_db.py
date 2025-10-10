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
        # Create sample users with extended registration data
        users_data = [
            {
                "email": "john@example.com",
                "name": "John Smith",
                "employment_status": "Employed full-time",
                "industry": "Marketing & Advertising",
                "role": "Marketing Manager",
                "primary_use_context": "Work",
                "tried_ai_before": True,
                "ai_tools_used": ["ChatGPT", "Midjourney"],
                "usage_frequency": "Weekly",
                "comfort_level": 2,
                "goals": [
                    "Automate repetitive tasks",
                    "Improve content creation",
                    "Learn prompt engineering"
                ],
                "challenges": ["Not sure where to start", "Overwhelming number of tools"],
                "learning_preference": "Hands-on projects",
                "additional_comments": "Excited to learn more about AI in marketing!",
                # Legacy fields
                "experience_level": "Beginner",
                "background": "Marketing professional interested in AI"
            },
            {
                "email": "sarah@example.com",
                "name": "Sarah Chen",
                "employment_status": "Employed full-time",
                "industry": "Technology",
                "role": "Software Engineer",
                "primary_use_context": "Work",
                "tried_ai_before": True,
                "ai_tools_used": ["GitHub Copilot", "ChatGPT", "Claude"],
                "usage_frequency": "Daily",
                "comfort_level": 4,
                "goals": [
                    "Build AI-powered applications",
                    "Understand LLM architecture",
                    "Implement RAG systems"
                ],
                "challenges": ["Understanding best practices", "Scaling AI applications"],
                "learning_preference": "Technical deep-dives",
                "additional_comments": "Looking forward to advanced topics!",
                # Legacy fields
                "experience_level": "Intermediate",
                "background": "Software developer with some ML experience"
            },
            {
                "email": "mike@example.com",
                "name": "Mike Johnson",
                "employment_status": "Employed full-time",
                "industry": "Research & Academia",
                "role": "Data Scientist",
                "primary_use_context": "Work",
                "tried_ai_before": True,
                "ai_tools_used": ["TensorFlow", "PyTorch", "OpenAI API", "Anthropic API"],
                "usage_frequency": "Daily",
                "comfort_level": 5,
                "goals": [
                    "Stay current with latest AI developments",
                    "Network with AI professionals",
                    "Explore cutting-edge research"
                ],
                "challenges": ["Keeping up with rapid changes"],
                "learning_preference": "Research papers & case studies",
                "additional_comments": "Interested in contributing to the community.",
                # Legacy fields
                "experience_level": "Advanced",
                "background": "Data scientist with AI research background"
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

            # Create experience profile with all extended fields
            experience = UserExperience(
                user_id=user.id,
                # Basic Info
                name=user_data["name"],
                employment_status=user_data["employment_status"],
                industry=user_data["industry"],
                role=user_data["role"],
                # Primary Use Context
                primary_use_context=user_data["primary_use_context"],
                # AI Experience
                tried_ai_before=user_data["tried_ai_before"],
                ai_tools_used=user_data["ai_tools_used"],
                usage_frequency=user_data["usage_frequency"],
                comfort_level=user_data["comfort_level"],
                # Goals & Applications
                goals=user_data["goals"],
                # Biggest Challenges
                challenges=user_data["challenges"],
                # Learning Preference
                learning_preference=user_data["learning_preference"],
                # Additional Comments
                additional_comments=user_data["additional_comments"],
                # Legacy fields
                experience_level=user_data["experience_level"],
                background=user_data["background"]
            )
            db.add(experience)

        # Create sample courses with categories matching Stripe products
        courses_data = [
            {
                "title": "Free AI Intro Course",
                "description": "Introduction to AI fundamentals - completely free",
                "category": "free",
                "stripe_product_id": None,  # Free courses don't need product link
                "schedule": "Self-paced",
                "materials_url": "https://example.com/free-intro"
            },
            {
                "title": "AI in 4 Weekends - Week 1: Foundations",
                "description": "Week 1 of the complete AI mastery program",
                "category": "curriculum",
                "stripe_product_id": None,  # Category-based access
                "schedule": "Weekend 1, Saturday 9:00 AM - 5:00 PM PST",
                "materials_url": "https://example.com/ai-4-weekends/week-1"
            },
            {
                "title": "AI in 4 Weekends - Week 2: Applications",
                "description": "Week 2 of the complete AI mastery program",
                "category": "curriculum",
                "stripe_product_id": None,  # Category-based access
                "schedule": "Weekend 2, Saturday 9:00 AM - 5:00 PM PST",
                "materials_url": "https://example.com/ai-4-weekends/week-2"
            },
            {
                "title": "AI in 4 Weekends - Week 3: Advanced Topics",
                "description": "Week 3 of the complete AI mastery program",
                "category": "curriculum",
                "stripe_product_id": None,  # Category-based access
                "schedule": "Weekend 3, Saturday 9:00 AM - 5:00 PM PST",
                "materials_url": "https://example.com/ai-4-weekends/week-3"
            },
            {
                "title": "AI in 4 Weekends - Week 4: Real-World Projects",
                "description": "Week 4 of the complete AI mastery program",
                "category": "curriculum",
                "stripe_product_id": None,  # Category-based access
                "schedule": "Weekend 4, Saturday 9:00 AM - 5:00 PM PST",
                "materials_url": "https://example.com/ai-4-weekends/week-4"
            },
            {
                "title": "Prompt Engineering Mastery",
                "description": "Deep dive into advanced prompt engineering techniques",
                "category": "alacarte",
                "stripe_product_id": None,  # Category-based access
                "schedule": "Self-paced with live Q&A sessions",
                "materials_url": "https://example.com/prompt-engineering"
            },
            {
                "title": "AI Automation for Business",
                "description": "Learn how to automate business processes with AI tools",
                "category": "alacarte",
                "stripe_product_id": None,  # Category-based access
                "schedule": "Self-paced with weekly office hours",
                "materials_url": "https://example.com/ai-automation"
            }
        ]

        for course_data in courses_data:
            course = Course(**course_data)
            db.add(course)

        await db.commit()
        print("✅ Database seeded successfully!")
        print(f"   Created {len(users_data)} users and {len(courses_data)} courses")
        print("   Course categories: 1 free, 4 curriculum, 2 alacarte")


if __name__ == "__main__":
    asyncio.run(seed_db())
