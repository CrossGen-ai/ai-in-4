from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import Course
from models.schemas import CourseResponse
from typing import List

router = APIRouter()


@router.get("/", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    """Get list of all available courses."""
    result = await db.execute(select(Course))
    courses = result.scalars().all()
    return [CourseResponse.model_validate(course) for course in courses]


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """Get course details by ID."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return CourseResponse.model_validate(course)
