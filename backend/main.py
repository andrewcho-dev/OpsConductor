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
from app.routers import users, auth, universal_targets, system, notifications, jobs, analytics, celery_monitor, job_safety_routes, job_scheduling_routes, discovery, system_health, log_viewer, audit
from app.api import system_simple as system_management
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
    
    # Initialize cache service
    from app.shared.infrastructure.cache import cache_service
    await cache_service.initialize()
    
    yield
    # Shutdown
    print("🛑 OpsConductor Platform shutting down...")

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
app.include_router(system.router)
app.include_router(notifications.router)
app.include_router(jobs.router)
app.include_router(analytics.router)
app.include_router(celery_monitor.router, prefix="/api")
app.include_router(job_safety_routes.router)
app.include_router(job_scheduling_routes.router)
app.include_router(discovery.router, tags=["Network Discovery"])
app.include_router(system_health.router, tags=["System Health"])
app.include_router(log_viewer.router, tags=["Log Viewer"])
app.include_router(audit.router, tags=["Audit"])
app.include_router(system_management.router, prefix="/api/system-management", tags=["System Management"])

# Include new versioned API routers
from app.api.v1 import (
    users as users_v1, 
    websocket as websocket_v1, 
    targets as targets_v1, 
    analytics as analytics_v1,
    monitoring as monitoring_v1,
    audit as audit_v1,
    device_types as device_types_v1
)
app.include_router(users_v1.router, tags=["Users API v1"])
app.include_router(websocket_v1.router, prefix="/api/v1", tags=["WebSocket API v1"])
app.include_router(targets_v1.router, tags=["Targets API v1"])
app.include_router(analytics_v1.router, tags=["Analytics API v1"])
app.include_router(monitoring_v1.router, tags=["Monitoring API v1"])
app.include_router(audit_v1.router, tags=["Audit API v1"])
app.include_router(device_types_v1.router, tags=["Device Types API v1"])

@app.get("/")
async def root():
    return {
        "message": "OpsConductor Universal Automation Orchestration Platform",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OpsConductor Platform"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "service": "OpsConductor Platform"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 