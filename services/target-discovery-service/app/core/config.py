"""
Configuration settings for Target Discovery Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "target-discovery-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://discovery_user:discovery_password@discovery-postgres:5432/discovery_db"
    )
    
    # Redis Configuration (for caching and job queue)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/7")
    
    # RabbitMQ Configuration
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/8")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/9")
    
    # Service URLs for inter-service communication
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    UNIVERSAL_TARGETS_SERVICE_URL: str = os.getenv("UNIVERSAL_TARGETS_SERVICE_URL", "http://universal-targets-service:3001")
    AUDIT_EVENTS_SERVICE_URL: str = os.getenv("AUDIT_EVENTS_SERVICE_URL", "http://audit-events-service:8004")
    
    # Discovery Configuration
    DEFAULT_DISCOVERY_TIMEOUT: float = float(os.getenv("DEFAULT_DISCOVERY_TIMEOUT", "3.0"))
    MAX_DISCOVERY_TIMEOUT: float = float(os.getenv("MAX_DISCOVERY_TIMEOUT", "30.0"))
    DEFAULT_MAX_CONCURRENT: int = int(os.getenv("DEFAULT_MAX_CONCURRENT", "100"))
    MAX_CONCURRENT_LIMIT: int = int(os.getenv("MAX_CONCURRENT_LIMIT", "1000"))
    
    # Network Scanning Configuration
    DEFAULT_COMMON_PORTS: List[int] = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306]
    DEFAULT_SNMP_COMMUNITIES: List[str] = ["public", "private"]
    SNMP_TIMEOUT: float = float(os.getenv("SNMP_TIMEOUT", "2.0"))
    SNMP_RETRIES: int = int(os.getenv("SNMP_RETRIES", "2"))
    
    # Discovery Job Configuration
    MAX_DISCOVERY_JOBS_PER_USER: int = int(os.getenv("MAX_DISCOVERY_JOBS_PER_USER", "10"))
    DISCOVERY_JOB_RETENTION_DAYS: int = int(os.getenv("DISCOVERY_JOB_RETENTION_DAYS", "90"))
    MAX_DEVICES_PER_JOB: int = int(os.getenv("MAX_DEVICES_PER_JOB", "10000"))
    
    # Device Detection Configuration
    ENABLE_OS_DETECTION: bool = os.getenv("ENABLE_OS_DETECTION", "true").lower() == "true"
    ENABLE_SERVICE_DETECTION: bool = os.getenv("ENABLE_SERVICE_DETECTION", "true").lower() == "true"
    ENABLE_HOSTNAME_RESOLUTION: bool = os.getenv("ENABLE_HOSTNAME_RESOLUTION", "true").lower() == "true"
    ENABLE_MAC_DETECTION: bool = os.getenv("ENABLE_MAC_DETECTION", "true").lower() == "true"
    
    # SNMP Configuration
    ENABLE_SNMP_DISCOVERY: bool = os.getenv("ENABLE_SNMP_DISCOVERY", "true").lower() == "true"
    SNMP_VERSION: str = os.getenv("SNMP_VERSION", "2c")  # 1, 2c, 3
    
    # Security Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your-encryption-key-here-32-chars")
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "500"))
    
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
    
    # Worker Configuration
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "4"))
    WORKER_PREFETCH_MULTIPLIER: int = int(os.getenv("WORKER_PREFETCH_MULTIPLIER", "1"))
    WORKER_MAX_TASKS_PER_CHILD: int = int(os.getenv("WORKER_MAX_TASKS_PER_CHILD", "1000"))
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9092"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()