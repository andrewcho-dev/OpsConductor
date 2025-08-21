"""
Configuration settings for User Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "user-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user_user:user_password@user-postgres:5432/user_db"
    )
    
    # Redis Configuration (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/2")
    
    # RabbitMQ Configuration
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # Service URLs for inter-service communication
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    AUDIT_EVENTS_SERVICE_URL: str = os.getenv("AUDIT_EVENTS_SERVICE_URL", "http://audit-events-service:8004")
    
    # User Configuration
    DEFAULT_USER_ROLE: str = os.getenv("DEFAULT_USER_ROLE", "user")
    MAX_USERS_PER_ORGANIZATION: int = int(os.getenv("MAX_USERS_PER_ORGANIZATION", "1000"))
    REQUIRE_EMAIL_VERIFICATION: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() == "true"
    
    # Profile Configuration
    MAX_PROFILE_PICTURE_SIZE_MB: int = int(os.getenv("MAX_PROFILE_PICTURE_SIZE_MB", "5"))
    ALLOWED_PROFILE_PICTURE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    
    # Security Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your-encryption-key-here-32-chars")
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "https://localhost:8443"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "15"))
    
    # API Key Configuration (for service-to-service auth)
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    INTERNAL_API_KEYS: List[str] = os.getenv("INTERNAL_API_KEYS", "").split(",") if os.getenv("INTERNAL_API_KEYS") else []
    
    # File Storage Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    
    # Notification Configuration
    SEND_WELCOME_EMAIL: bool = os.getenv("SEND_WELCOME_EMAIL", "true").lower() == "true"
    SEND_PROFILE_UPDATE_NOTIFICATIONS: bool = os.getenv("SEND_PROFILE_UPDATE_NOTIFICATIONS", "false").lower() == "true"
    
    # Role and Permission Configuration
    ENABLE_DYNAMIC_PERMISSIONS: bool = os.getenv("ENABLE_DYNAMIC_PERMISSIONS", "true").lower() == "true"
    MAX_ROLES_PER_USER: int = int(os.getenv("MAX_ROLES_PER_USER", "10"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()