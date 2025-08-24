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
    # Removed: rabbitmq_url - Using direct HTTP communication
    
    # External Services
    job_management_service_url: str = "http://localhost:8001"
    target_service_url: str = "http://localhost:3001"
    
    # Execution Configuration
    max_concurrent_targets: int = 10
    connection_timeout: int = 30
    command_timeout: int = 300
    enable_retry: bool = True
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    enable_safety_checks: bool = True
    
    # Safety Configuration
    dangerous_commands: List[str] = [
        "rm -rf /", "del /f /s /q c:\\", "format c:", 
        "shutdown", "reboot", "halt", "poweroff"
    ]
    
    # Authentication
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"


settings = Settings()