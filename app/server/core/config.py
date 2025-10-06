from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "App API"
    VERSION: str = "0.1.0"

    # Server Configuration (from environment)
    SERVER_PORT: int = 8000
    SERVER_HOST: str = "0.0.0.0"
    SERVER_RELOAD: bool = True

    # CORS - Parse comma-separated origins from env
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Magic Link Authentication
    MAGIC_LINK_SECRET: str = "your-secret-key-change-in-production"
    MAGIC_LINK_EXPIRY_MINUTES: int = 15

    # Email Configuration
    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 587
    EMAIL_FROM: str = "noreply@crossgen-ai.com"
    EMAIL_USE_TLS: bool = True
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    # Development mode
    DEV_MODE: bool = True

    # Optional API Keys (for other features)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
