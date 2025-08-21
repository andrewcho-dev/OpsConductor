"""
User Service Configuration
"""
import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user_user:user_password@user-postgres:5432/user_db"
    )
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Service Configuration
    SERVICE_NAME: str = "user-service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://localhost",
        "http://localhost",
        "https://localhost:443",
        "http://localhost:80"
    ]
    
    # Auth Service Integration
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    
    # Redis (for caching if needed)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/1")
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 25
    MAX_PAGE_SIZE: int = 1000
    
    class Config:
        env_file = ".env"


settings = Settings()