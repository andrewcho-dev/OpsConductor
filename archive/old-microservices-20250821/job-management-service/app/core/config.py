"""
Job Management Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Job Management Service settings"""
    
    # Service Info
    service_name: str = "job-management-service"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/job_management"
    
    # Message Broker
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    
    # External Services
    job_execution_service_url: str = "http://localhost:8002"
    job_scheduling_service_url: str = "http://localhost:8003"
    audit_events_service_url: str = "http://localhost:8004"
    target_service_url: str = "http://localhost:3001"
    user_service_url: str = "http://localhost:3002"
    
    # Authentication
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"


settings = Settings()