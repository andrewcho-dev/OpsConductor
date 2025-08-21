"""
Configuration settings for Job Execution Service
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # =============================================================================
    # SERVICE CONFIGURATION
    # =============================================================================
    service_name: str = "job-execution-service"
    version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://job_user:job_password@localhost:5433/job_execution_db"
    )
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6380/0")
    
    # =============================================================================
    # EXTERNAL SERVICES
    # =============================================================================
    target_service_url: str = os.getenv("TARGET_SERVICE_URL", "http://localhost:8000")
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    notification_service_url: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8000")
    
    # =============================================================================
    # JWT CONFIGURATION
    # =============================================================================
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # =============================================================================
    # EXECUTION CONFIGURATION
    # =============================================================================
    max_concurrent_targets: int = int(os.getenv("MAX_CONCURRENT_TARGETS", "10"))
    connection_timeout: int = int(os.getenv("CONNECTION_TIMEOUT", "30"))
    command_timeout: int = int(os.getenv("COMMAND_TIMEOUT", "300"))
    
    # Retry Configuration
    enable_retry: bool = os.getenv("ENABLE_RETRY", "true").lower() == "true"
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_backoff_base: float = float(os.getenv("RETRY_BACKOFF_BASE", "2.0"))
    
    # =============================================================================
    # CELERY CONFIGURATION
    # =============================================================================
    celery_broker_url: str = redis_url
    celery_result_backend: str = redis_url
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "9090"))
    
    # =============================================================================
    # SAFETY CONFIGURATION
    # =============================================================================
    enable_safety_checks: bool = os.getenv("ENABLE_SAFETY_CHECKS", "true").lower() == "true"
    dangerous_commands: list = [
        "rm -rf /",
        "format c:",
        "del /f /s /q c:\\*",
        "shutdown",
        "reboot",
        "halt",
        "poweroff"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()