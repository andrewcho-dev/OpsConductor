"""
Configuration settings for Audit Events Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "audit-events-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://audit_user:audit_password@audit-postgres:5432/audit_db"
    )
    
    # Redis Configuration (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/6")
    
    # Removed: RabbitMQ - Using direct HTTP communication
    
    # Service URLs for inter-service communication
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    
    # Audit Configuration
    AUDIT_RETENTION_DAYS: int = int(os.getenv("AUDIT_RETENTION_DAYS", "365"))  # 1 year default
    MAX_EVENT_SIZE_KB: int = int(os.getenv("MAX_EVENT_SIZE_KB", "100"))
    ENABLE_REAL_TIME_STREAMING: bool = os.getenv("ENABLE_REAL_TIME_STREAMING", "true").lower() == "true"
    
    # Event Processing Configuration
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    BATCH_TIMEOUT_SECONDS: int = int(os.getenv("BATCH_TIMEOUT_SECONDS", "5"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    
    # Compliance Configuration
    ENABLE_COMPLIANCE_LOGGING: bool = os.getenv("ENABLE_COMPLIANCE_LOGGING", "true").lower() == "true"
    COMPLIANCE_STANDARDS: List[str] = os.getenv("COMPLIANCE_STANDARDS", "SOX,HIPAA,PCI-DSS").split(",")
    ENABLE_DATA_ENCRYPTION: bool = os.getenv("ENABLE_DATA_ENCRYPTION", "true").lower() == "true"
    
    # Security Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your-encryption-key-here-32-chars")
    ENABLE_EVENT_SIGNING: bool = os.getenv("ENABLE_EVENT_SIGNING", "true").lower() == "true"
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "1000"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "https://localhost:8443"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "15"))
    
    # API Key Configuration (for service-to-service auth)
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    INTERNAL_API_KEYS: List[str] = os.getenv("INTERNAL_API_KEYS", "").split(",") if os.getenv("INTERNAL_API_KEYS") else []
    
    # Alerting Configuration
    ENABLE_SECURITY_ALERTS: bool = os.getenv("ENABLE_SECURITY_ALERTS", "true").lower() == "true"
    ALERT_WEBHOOK_URL: str = os.getenv("ALERT_WEBHOOK_URL", "")
    CRITICAL_EVENT_THRESHOLD: int = int(os.getenv("CRITICAL_EVENT_THRESHOLD", "10"))
    
    # Export Configuration
    ENABLE_EVENT_EXPORT: bool = os.getenv("ENABLE_EVENT_EXPORT", "true").lower() == "true"
    EXPORT_FORMATS: List[str] = ["json", "csv", "xml"]
    MAX_EXPORT_RECORDS: int = int(os.getenv("MAX_EXPORT_RECORDS", "10000"))
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9091"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()