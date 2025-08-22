"""
Job Execution Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Job Execution Service settings"""
    
    # Service Info
    service_name: str = "job-execution-service"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8002
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/job_execution"
    
    # Redis
    redis_url: str = "redis://localhost:6379/1"
    
    # Message Broker
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    
    # External Services
    auth_service_url: str = "http://auth-service:8000"
    user_service_url: str = "http://user-service:8000"
    targets_service_url: str = "http://targets-service:8000"
    jobs_service_url: str = "http://jobs-service:8000"
    execution_service_url: str = "http://execution-service:8000"
    audit_service_url: str = "http://audit-events-service:8000"
    notification_service_url: str = "http://notification-service:8000"
    target_discovery_service_url: str = "http://target-discovery-service:8000"
    
    # Legacy compatibility
    job_management_service_url: str = "http://jobs-service:8000"
    target_service_url: str = "http://targets-service:8000"
    
    # Execution Configuration
    max_concurrent_targets: int = 50
    connection_timeout: int = 30
    command_timeout: int = 600
    enable_retry: bool = True
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    enable_safety_checks: bool = True
    
    # Celery Worker Configuration
    celery_worker_concurrency: int = 8
    celery_worker_prefetch_multiplier: int = 1
    celery_task_acks_late: bool = True
    celery_result_expires: int = 3600
    
    # Discovery Configuration
    auto_discovery_networks: List[str] = ["192.168.1.0/24", "10.0.0.0/24"]
    discovery_scan_timeout: int = 30
    discovery_max_concurrent: int = 20
    
    # Safety Configuration
    dangerous_commands: List[str] = [
        "rm -rf /", "del /f /s /q c:\\", "format c:", 
        "shutdown", "reboot", "halt", "poweroff"
    ]
    
    # Authentication
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    
    # Object Storage (MinIO/S3)
    object_storage_enabled: bool = True
    minio_endpoint: str = "http://minio:9000"
    minio_access_key: str = "opsconductor"
    minio_secret_key: str = "opsconductor_minio_2024_secure"
    minio_secure: bool = False
    minio_region: str = "us-east-1"
    object_storage_bucket_prefix: str = "opsconductor"
    object_storage_size_threshold: str = "64KB"  # Files larger than this go to object storage
    object_storage_temp_bucket: str = "opsconductor-temp"
    object_storage_artifacts_bucket: str = "opsconductor-artifacts"
    object_storage_logs_bucket: str = "opsconductor-logs"
    object_storage_executions_bucket: str = "opsconductor-executions"
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"


settings = Settings()