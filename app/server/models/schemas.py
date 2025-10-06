from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Define your Pydantic models here
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: Optional[str] = None


# User Schemas
class UserExperienceCreate(BaseModel):
    experience_level: str  # Beginner, Intermediate, Advanced
    background: Optional[str] = None
    goals: Optional[str] = None


class UserExperienceResponse(BaseModel):
    id: int
    user_id: int
    experience_level: str
    background: Optional[str] = None
    goals: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    experience_level: str
    background: Optional[str] = None
    goals: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Magic Link Schemas
class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkValidate(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    user: UserResponse


# Course Schemas
class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    schedule: Optional[str] = None
    materials_url: Optional[str] = None

    class Config:
        from_attributes = True
