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

    # Stripe and referral fields
    referral_code = Column(String(8), unique=True, index=True, nullable=True)
    referral_credits = Column(Integer, default=0)
    stripe_customer_id = Column(String(255), unique=True, nullable=True)

    # Relationships
    experience = relationship("UserExperience", back_populates="user", uselist=False)
    magic_links = relationship("MagicLink", back_populates="user")
    entitlements = relationship("Entitlement", back_populates="user")
    referrals_given = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")


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
    category = Column(String(50), nullable=False)  # free, curriculum, alacarte, unique
    stripe_product_id = Column(String(255), ForeignKey("stripe_products.id"), nullable=True, index=True)
    schedule = Column(Text, nullable=True)
    materials_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    stripe_product = relationship("StripeProduct", foreign_keys=[stripe_product_id])


class Entitlement(Base):
    __tablename__ = "entitlements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_price_id = Column(String(255), index=True, nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="active")  # active, expired, refunded
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    user = relationship("User", back_populates="entitlements")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referee_email = Column(String(255), nullable=False)
    course_id = Column(String(255), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")  # pending, confirmed, credited
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_given")


class StripeProduct(Base):
    __tablename__ = "stripe_products"

    id = Column(String(255), primary_key=True)  # Stripe product ID
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # free, curriculum, alacarte
    active = Column(Boolean, default=True)
    stripe_metadata = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    prices = relationship("StripePrice", back_populates="product")


class StripePrice(Base):
    __tablename__ = "stripe_prices"

    id = Column(String(255), primary_key=True)  # Stripe price ID
    product_id = Column(String(255), ForeignKey("stripe_products.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # in cents
    currency = Column(String(3), default="usd")
    active = Column(Boolean, default=True)
    stripe_metadata = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    product = relationship("StripeProduct", back_populates="prices")
