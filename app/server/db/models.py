from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    experience = relationship("UserExperience", back_populates="user", uselist=False)
    magic_links = relationship("MagicLink", back_populates="user")


class UserExperience(Base):
    __tablename__ = "user_experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Legacy fields (kept for backward compatibility)
    experience_level = Column(String(50), nullable=True)  # Beginner, Intermediate, Advanced (now optional/deprecated)
    background = Column(Text, nullable=True)

    # New extended registration fields
    # Basic Info
    name = Column(String(100), nullable=True)  # Made nullable for backward compatibility with existing records
    employment_status = Column(String(50), nullable=True)
    employment_status_other = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)

    # Primary Use Context
    primary_use_context = Column(String(50), nullable=True)

    # AI Experience
    tried_ai_before = Column(Boolean, nullable=True)
    ai_tools_used = Column(JSON, nullable=True)  # Array of strings
    usage_frequency = Column(String(50), nullable=True)
    comfort_level = Column(Integer, nullable=True)  # 1-5

    # Goals & Applications
    goals = Column(JSON, nullable=True)  # Array of strings, exactly 3 items

    # Biggest Challenges
    challenges = Column(JSON, nullable=True)  # Array of strings

    # Learning Preference
    learning_preference = Column(String(50), nullable=True)

    # Additional Comments
    additional_comments = Column(Text, nullable=True)  # 500 chars max

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    user = relationship("User", back_populates="experience")


class MagicLink(Base):
    __tablename__ = "magic_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    used = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="magic_links")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    schedule = Column(Text, nullable=True)
    materials_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
