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
from app.routers import users, auth, universal_targets, audit
# Legacy routers removed - consolidated into V2 APIs
# Legacy system_health and system_management removed - consolidated into V2 APIs
from app.core.config import settings
from app.core.security import verify_token

# Import models to ensure they are registered with SQLAlchemy
from app.models import notification_models, user_models, job_models, analytics_models, job_schedule_models, discovery_models

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
    
    yield
    
    # Shutdown
    print("🛑 OpsConductor Platform shutting down...")
    
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency to verify JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(universal_targets.router, tags=["Universal Targets"])
app.include_router(audit.router, tags=["Audit v1"])
# Legacy routers removed - consolidated into V2 APIs
# system.router -> /api/v2/system/*
# notifications.router -> /api/v2/notifications/*  
# discovery.router -> /api/v2/discovery/*
# Legacy health/metrics/log_viewer routers removed - consolidated into V2 APIs

# Include enhanced V2 API routers
from app.api.v2 import (
    websocket_enhanced as websocket_v2,
    audit_enhanced as audit_v2,
    device_types_enhanced as device_types_v2,
    health_enhanced as health_v2,
    metrics_enhanced as metrics_v2,
    jobs_enhanced as jobs_v2,
    templates_enhanced as templates_v2,
    system_enhanced as system_v2,
    discovery_enhanced as discovery_v2,
    notifications_enhanced as notifications_v2,
    log_viewer_enhanced as log_viewer_v2
)
from app.api.v1 import (
    celery_monitor,
    system_info
)
# Include enhanced V2 routers (routers already have their own prefixes)
app.include_router(websocket_v2.router, tags=["WebSocket API v2"])
app.include_router(audit_v2.router, tags=["Audit API v2"])
app.include_router(device_types_v2.router, tags=["Device Types API v2"])
app.include_router(health_v2.router, tags=["Health & Monitoring v2"])
app.include_router(metrics_v2.router, tags=["Metrics & Analytics v2"])
app.include_router(jobs_v2.router, tags=["Jobs Management v2"])
app.include_router(templates_v2.router, tags=["Templates Management v2"])
app.include_router(system_v2.router, tags=["System Administration v2"])
app.include_router(discovery_v2.router, tags=["Network Discovery v2"])
app.include_router(notifications_v2.router, tags=["Notifications & Alerts v2"])
app.include_router(log_viewer_v2.router, tags=["Log Viewer v2"])

# Include V1 compatibility routers
app.include_router(celery_monitor.router, tags=["Celery Monitoring"])
app.include_router(system_info.router, tags=["System Info"])

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

# Legacy health endpoints removed - use /api/v2/health/ instead

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 