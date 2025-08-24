"""
Configuration settings for Job Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "job-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://job_user:job_password@job-postgres:5432/job_db"
    )
    
    # Redis Configuration (for caching and job queue)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/3")
    
    # RabbitMQ Configuration
    # Removed: RABBITMQ_URL - Using direct HTTP communication
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/4")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/5")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    
    # Service URLs for inter-service communication
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    UNIVERSAL_TARGETS_SERVICE_URL: str = os.getenv("UNIVERSAL_TARGETS_SERVICE_URL", "http://universal-targets-service:3001")
    AUDIT_EVENTS_SERVICE_URL: str = os.getenv("AUDIT_EVENTS_SERVICE_URL", "http://audit-events-service:8004")
    
    # Job Configuration
    DEFAULT_JOB_TIMEOUT_MINUTES: int = int(os.getenv("DEFAULT_JOB_TIMEOUT_MINUTES", "60"))
    MAX_JOB_TIMEOUT_MINUTES: int = int(os.getenv("MAX_JOB_TIMEOUT_MINUTES", "1440"))  # 24 hours
    DEFAULT_JOB_PRIORITY: int = int(os.getenv("DEFAULT_JOB_PRIORITY", "5"))
    MAX_RETRY_COUNT: int = int(os.getenv("MAX_RETRY_COUNT", "3"))
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "10"))
    MAX_ACTIONS_PER_JOB: int = int(os.getenv("MAX_ACTIONS_PER_JOB", "50"))
    MAX_TARGETS_PER_JOB: int = int(os.getenv("MAX_TARGETS_PER_JOB", "1000"))
    
    # Execution Configuration
    EXECUTION_CLEANUP_DAYS: int = int(os.getenv("EXECUTION_CLEANUP_DAYS", "30"))
    MAX_OUTPUT_SIZE_KB: int = int(os.getenv("MAX_OUTPUT_SIZE_KB", "1024"))  # 1MB
    EXECUTION_HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv("EXECUTION_HEARTBEAT_INTERVAL_SECONDS", "30"))
    
    # Scheduling Configuration
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "UTC")
    MAX_SCHEDULE_LOOKAHEAD_DAYS: int = int(os.getenv("MAX_SCHEDULE_LOOKAHEAD_DAYS", "7"))
    
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
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    
    # Worker Configuration
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "4"))
    WORKER_PREFETCH_MULTIPLIER: int = int(os.getenv("WORKER_PREFETCH_MULTIPLIER", "1"))
    WORKER_MAX_TASKS_PER_CHILD: int = int(os.getenv("WORKER_MAX_TASKS_PER_CHILD", "1000"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()