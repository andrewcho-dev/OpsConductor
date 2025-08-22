from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database - NO HARDCODED VALUES!
    DATABASE_URL: str
    
    # Redis - NO HARDCODED VALUES!
    REDIS_URL: str
    
    # Security - NO HARDCODED VALUES!
    SECRET_KEY: str
    
    # Auth Service
    AUTH_SERVICE_URL: str = "http://opsconductor-auth-service:8000"
    
    # CORS
    CORS_ORIGINS: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Job Execution
    MAX_CONCURRENT_TARGETS: int = 20
    CONNECTION_TIMEOUT: int = 30
    COMMAND_TIMEOUT: int = 300
    
    # Retry Configuration
    ENABLE_RETRY: bool = False
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0
    
    class Config:
        env_file = ".env"


settings = Settings() 