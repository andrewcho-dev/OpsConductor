"""
OpsConductor - Enterprise Automation Orchestration Platform
Copyright © 2025 Enabled Enterprises LLC. All rights reserved.

Licensed under the MIT License.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os
from typing import List

# Import new middleware
from app.shared.middleware.error_handler import ErrorHandlingMiddleware, RequestLoggingMiddleware

from app.database.database import engine, Base
# LEGACY ROUTERS REMOVED - Using v3 only
# Legacy routers removed - consolidated into V2 APIs
# Legacy system_health and system_management removed - consolidated into V2 APIs
from app.core.config import settings
# Import centralized authentication
from app.core.auth_dependencies import get_current_user

# Import models to ensure they are registered with SQLAlchemy
from app.models import notification_models, job_models, analytics_models, job_schedule_models, discovery_models

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 OpsConductor Platform starting up...")
    
    # Initialize existing cache service
    from app.shared.infrastructure.cache import cache_service
    await cache_service.initialize()
    
    # Initialize Phase 2 improvements - Redis cache for device types
    try:
        from app.core.cache import initialize_redis
        await initialize_redis()
        print("✅ Device Types Redis cache initialized")
    except Exception as e:
        print(f"⚠️  Device Types Redis cache initialization failed: {e}")
    
    # Initialize structured logging
    try:
        from app.core.logging import app_logger
        app_logger.info("OpsConductor Platform startup completed with Phase 2 improvements")
        print("✅ Structured logging initialized")
    except Exception as e:
        print(f"⚠️  Structured logging initialization failed: {e}")
    
    # Log system startup event
    try:
        from sqlalchemy.orm import Session
        from app.database.database import SessionLocal
        from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
        import platform
        import socket
        import os
        
        # Get system information
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        os_info = f"{platform.system()} {platform.release()}"
        python_version = platform.python_version()
        
        # Create database session
        db = SessionLocal()
        
        # Log startup event
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_STARTUP,
            user_id=None,  # System event
            resource_type="system",
            resource_id="startup",
            action="system_startup",
            details={
                "hostname": hostname,
                "ip_address": ip_address,
                "os_info": os_info,
                "python_version": python_version,
                "pid": os.getpid()
            },
            severity=AuditSeverity.INFO
        )
        
        # Close database session
        db.close()
        print("✅ System startup audit event logged")
    except Exception as e:
        print(f"⚠️  Failed to log system startup event: {e}")
    
    yield
    
    # Shutdown
    print("🛑 OpsConductor Platform shutting down...")
    
    # Log system shutdown event
    try:
        from sqlalchemy.orm import Session
        from app.database.database import SessionLocal
        from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
        import platform
        import socket
        import os
        
        # Get system information
        hostname = socket.gethostname()
        
        # Create database session
        db = SessionLocal()
        
        # Log shutdown event
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_SHUTDOWN,
            user_id=None,  # System event
            resource_type="system",
            resource_id="shutdown",
            action="system_shutdown",
            details={
                "hostname": hostname,
                "pid": os.getpid()
            },
            severity=AuditSeverity.INFO
        )
        
        # Close database session
        db.close()
        print("✅ System shutdown audit event logged")
    except Exception as e:
        print(f"⚠️  Failed to log system shutdown event: {e}")
    
    # Close Redis connections
    try:
        from app.core.cache import close_redis
        await close_redis()
        print("✅ Device Types Redis cache closed")
    except Exception as e:
        print(f"⚠️  Redis cache cleanup failed: {e}")

app = FastAPI(
    title="OpsConductor Enterprise Automation Orchestration Platform",
    description="Job-centric automation platform for orchestrating tasks across any type of target system",
    version="1.0.0",
    lifespan=lifespan,
    root_path=""
)

# CORS middleware - Environment-aware configuration
def get_cors_origins():
    if settings.CORS_ORIGINS:
        return [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    elif settings.ENVIRONMENT == "development":
        # In development, allow all origins for flexibility
        return ["*"]
    else:
        # In production, be more restrictive - only allow same origin
        return []

# Add custom middleware (order matters - first added is outermost)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add audit middleware for API access logging
from app.core.audit_middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Authentication is now handled by centralized auth_dependencies module

# LEGACY ROUTERS REMOVED - Using v3 only
# Legacy routers removed - using v3 only

# V2 APIs REMOVED - Using v3 only
# V1 APIs REMOVED - Using v3 only
from app.api.v3 import (
    jobs_simple as jobs_v3,
    schedules as schedules_v3,

    targets as targets_v3,

    system as system_v3,
    celery as celery_v3,
    audit as audit_v3,
    discovery as discovery_v3,
    notifications as notifications_v3,
    templates as templates_v3,
    metrics as metrics_v3,
    websocket as websocket_v3,
    device_types as device_types_v3,
    docker as docker_v3,

    analytics as analytics_v3,
    data_export as data_export_v3
)
# V2 ROUTERS REMOVED - Using v3 only

# Include V3 consolidated APIs
app.include_router(jobs_v3.router, tags=["Jobs v3 - Simplified"])
app.include_router(schedules_v3.router, tags=["Schedules v3"])
# Users management moved to auth service - NO LONGER IN MAIN BACKEND
app.include_router(targets_v3.router, tags=["Targets v3"])

app.include_router(system_v3.router, tags=["System v3"])
app.include_router(celery_v3.router, tags=["Celery v3"])
app.include_router(audit_v3.router, tags=["Audit v3"])
app.include_router(discovery_v3.router, tags=["Discovery v3"])
app.include_router(notifications_v3.router, tags=["Notifications v3"])
app.include_router(templates_v3.router, tags=["Templates v3"])
app.include_router(metrics_v3.router, tags=["Metrics v3"])
app.include_router(websocket_v3.router, tags=["WebSocket v3"])
app.include_router(device_types_v3.router, tags=["Device Types v3"])
app.include_router(docker_v3.router, tags=["Docker v3"])

app.include_router(analytics_v3.router, tags=["Analytics v3"])
app.include_router(data_export_v3.router, tags=["Data Export v3"])

# V1 ROUTERS REMOVED - Using v3 only

@app.get("/")
async def root():
    return {
        "message": "OpsConductor Universal Automation Orchestration Platform",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint for Docker health checks"""
    return {"status": "healthy", "service": "opsconductor-backend"}

# Legacy health endpoints removed - using v3 only

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 