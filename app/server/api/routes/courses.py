from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import Course, User, StripeProduct, StripePrice
from models.schemas import CourseResponse, CourseWithAccessResponse, StripeProductResponse, CourseAccessResponse
from api.routes.users import get_current_user
from services import entitlement_service
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    """Get list of all available courses."""
    result = await db.execute(select(Course))
    courses = result.scalars().all()
    return [CourseResponse.model_validate(course) for course in courses]


@router.get("/with-access", response_model=List[CourseWithAccessResponse])
async def list_courses_with_access(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all courses with access status for the current user.

    This endpoint uses category-based access logic:
    - free: Always accessible
    - unique: Must have entitlement to specific product
    - curriculum/alacarte: Must have entitlement to ANY product in same category
    """
    result = await db.execute(select(Course))
    courses = result.scalars().all()

    courses_with_access = []
    for course in courses:
        # Check access for authenticated users, always deny for anonymous
        has_access = False
        if current_user:
            has_access = await entitlement_service.check_course_access(
                current_user.id, course, db
            )

        courses_with_access.append(
            CourseWithAccessResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                category=course.category,
                schedule=course.schedule,
                materials_url=course.materials_url,
                has_access=has_access,
            )
        )

    return courses_with_access


@router.get("/products", response_model=List[StripeProductResponse])
async def list_course_products(db: AsyncSession = Depends(get_db)):
    """
    Get list of all course products with pricing.

    Returns:
        List of products with prices from Stripe
    """
    result = await db.execute(
        select(StripeProduct).where(StripeProduct.active)
    )
    products = result.scalars().all()

    # Enrich with price information
    response = []
    for product in products:
        # Get first active price for this product
        price_result = await db.execute(
            select(StripePrice)
            .where(
                StripePrice.product_id == product.id,
                StripePrice.active
            )
            .limit(1)
        )
        price = price_result.scalar_one_or_none()

        response.append(
            StripeProductResponse(
                id=product.id,
                name=product.name,
                description=product.description,
                category=product.category,
                price=price.amount if price else None,
                price_id=price.id if price else None,
                currency=price.currency if price else "usd",
            )
        )

    return response


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


@router.get("/{course_id}/check-access", response_model=CourseAccessResponse)
async def check_course_access(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if user has access to a course.

    Args:
        course_id: Course ID (maps to product ID)
        current_user: Authenticated user
        db: Database session

    Returns:
        Access status
    """
    # For now, course_id maps to product_id
    # In production, you'd have a proper mapping table
    product_id = f"prod_{course_id}"

    has_access = await entitlement_service.check_product_access(
        current_user.id, product_id, db
    )

    return CourseAccessResponse(has_access=has_access)
