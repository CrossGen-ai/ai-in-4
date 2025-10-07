from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
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
    # Contact Information
    email: EmailStr = Field(..., max_length=150)

    # Basic Info
    name: str = Field(..., min_length=1, max_length=100)
    employment_status: str = Field(..., max_length=50)
    employment_status_other: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=100)

    # Primary Use Context
    primary_use_context: str = Field(..., max_length=50)

    # AI Experience
    tried_ai_before: bool
    ai_tools_used: Optional[List[str]] = None
    usage_frequency: Optional[str] = Field(None, max_length=50)
    comfort_level: Optional[int] = Field(None, ge=1, le=5)

    # Goals & Applications
    goals: List[str] = Field(..., min_length=3, max_length=3)

    # Biggest Challenges
    challenges: Optional[List[str]] = None

    # Learning Preference
    learning_preference: str = Field(..., max_length=50)

    # Additional Comments
    additional_comments: Optional[str] = Field(None, max_length=500)

    # Legacy fields (optional for backward compatibility)
    experience_level: Optional[str] = Field(None, max_length=50)
    background: Optional[str] = None

    @field_validator('goals')
    @classmethod
    def validate_goals_count(cls, v):
        if len(v) != 3:
            raise ValueError('goals must contain exactly 3 items')
        return v

    @field_validator('ai_tools_used')
    @classmethod
    def validate_ai_tools_used(cls, v, info):
        # Only allow ai_tools_used if tried_ai_before is True
        # Note: tried_ai_before is validated before this field
        if v is not None and len(v) > 0:
            # If ai_tools_used has items, tried_ai_before must be True
            # This validation will be checked in service layer where we have access to all fields
            pass
        return v

    @field_validator('usage_frequency')
    @classmethod
    def validate_usage_frequency(cls, v, info):
        # If tried_ai_before is True, usage_frequency is required
        tried_ai_before = info.data.get('tried_ai_before')
        if tried_ai_before is True and not v:
            raise ValueError('usage_frequency is required when tried_ai_before is True')
        return v

    @field_validator('comfort_level')
    @classmethod
    def validate_comfort_level(cls, v, info):
        # If tried_ai_before is True, comfort_level is required
        tried_ai_before = info.data.get('tried_ai_before')
        if tried_ai_before is True and v is None:
            raise ValueError('comfort_level is required when tried_ai_before is True')
        return v


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
