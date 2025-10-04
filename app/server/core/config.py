from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "App API"
    VERSION: str = "0.1.0"

    # Server Configuration (from environment)
    SERVER_PORT: int = 8000
    SERVER_HOST: str = "0.0.0.0"
    SERVER_RELOAD: bool = True

    # CORS - Parse comma-separated origins from env
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Add your settings here (API keys, database, etc.)

    class Config:
        env_file = ".env"
        case_sensitive = True

    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

settings = Settings()
