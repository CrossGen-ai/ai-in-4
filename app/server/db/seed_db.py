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
