"""
Configuration settings for Notification Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "notification-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://notification_user:notification_password@notification-postgres:5432/notification_db"
    )
    
    # Redis Configuration (for caching and job queue)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/10")
    
    # RabbitMQ Configuration
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/11")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/12")
    
    # Service URLs for inter-service communication
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    AUDIT_EVENTS_SERVICE_URL: str = os.getenv("AUDIT_EVENTS_SERVICE_URL", "http://audit-events-service:8004")
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    DEFAULT_FROM_EMAIL: str = os.getenv("DEFAULT_FROM_EMAIL", "noreply@opsconductor.com")
    DEFAULT_FROM_NAME: str = os.getenv("DEFAULT_FROM_NAME", "OpsConductor")
    
    # SMS Configuration
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "twilio")  # twilio, aws_sns, etc.
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    
    # Webhook Configuration
    WEBHOOK_TIMEOUT_SECONDS: int = int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "30"))
    WEBHOOK_RETRY_COUNT: int = int(os.getenv("WEBHOOK_RETRY_COUNT", "3"))
    WEBHOOK_RETRY_DELAY_SECONDS: int = int(os.getenv("WEBHOOK_RETRY_DELAY_SECONDS", "60"))
    
    # Slack Configuration
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    
    # Microsoft Teams Configuration
    TEAMS_WEBHOOK_URL: str = os.getenv("TEAMS_WEBHOOK_URL", "")
    
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    
    # Push Notification Configuration
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    APNS_KEY_PATH: str = os.getenv("APNS_KEY_PATH", "")
    APNS_KEY_ID: str = os.getenv("APNS_KEY_ID", "")
    APNS_TEAM_ID: str = os.getenv("APNS_TEAM_ID", "")
    
    # Notification Configuration
    DEFAULT_NOTIFICATION_PRIORITY: int = int(os.getenv("DEFAULT_NOTIFICATION_PRIORITY", "5"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    NOTIFICATION_BATCH_SIZE: int = int(os.getenv("NOTIFICATION_BATCH_SIZE", "100"))
    NOTIFICATION_RATE_LIMIT: int = int(os.getenv("NOTIFICATION_RATE_LIMIT", "1000"))  # Per hour
    
    # Template Configuration
    TEMPLATE_CACHE_TTL_SECONDS: int = int(os.getenv("TEMPLATE_CACHE_TTL_SECONDS", "3600"))
    MAX_TEMPLATE_SIZE_KB: int = int(os.getenv("MAX_TEMPLATE_SIZE_KB", "100"))
    
    # Alert Configuration
    ALERT_COOLDOWN_MINUTES: int = int(os.getenv("ALERT_COOLDOWN_MINUTES", "60"))
    MAX_ALERTS_PER_RULE_PER_HOUR: int = int(os.getenv("MAX_ALERTS_PER_RULE_PER_HOUR", "10"))
    
    # Queue Configuration
    DEFAULT_QUEUE_SIZE: int = int(os.getenv("DEFAULT_QUEUE_SIZE", "10000"))
    HIGH_PRIORITY_QUEUE_SIZE: int = int(os.getenv("HIGH_PRIORITY_QUEUE_SIZE", "1000"))
    PROCESSING_RATE_PER_MINUTE: int = int(os.getenv("PROCESSING_RATE_PER_MINUTE", "100"))
    
    # Security Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your-encryption-key-here-32-chars")
    WEBHOOK_SECRET_KEY: str = os.getenv("WEBHOOK_SECRET_KEY", "your-webhook-secret-key")
    
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
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
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
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9093"))
    
    # Cleanup Configuration
    NOTIFICATION_LOG_RETENTION_DAYS: int = int(os.getenv("NOTIFICATION_LOG_RETENTION_DAYS", "90"))
    ALERT_LOG_RETENTION_DAYS: int = int(os.getenv("ALERT_LOG_RETENTION_DAYS", "365"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()