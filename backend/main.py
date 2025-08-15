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
from app.routers import users, auth, universal_targets
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
# Legacy routers removed - consolidated into V2 APIs
# system.router -> /api/v2/system/*
# notifications.router -> /api/v2/notifications/*  
# discovery.router -> /api/v2/discovery/*
# Legacy health/metrics/log_viewer routers removed - consolidated into V2 APIs

# Include remaining versioned API routers
from app.api.v1 import (
    websocket as websocket_v1, 
    # analytics removed - use /api/v2/metrics/ instead
    # monitoring removed - use /api/v2/metrics/ instead
    audit as audit_v1,
    device_types as device_types_v1
)
app.include_router(websocket_v1.router, prefix="/api/v1", tags=["WebSocket API v1"])
# Legacy analytics v1 removed - use /api/v2/metrics/ instead
app.include_router(audit_v1.router, tags=["Audit API v1"])
app.include_router(device_types_v1.router, tags=["Device Types API v1"])

# Include new V2 consolidated API routers
from app.api.v2 import (
    health as health_v2,
    metrics as metrics_v2,
    jobs as jobs_v2,
    templates as templates_v2,
    system as system_v2,
    discovery as discovery_v2,
    notifications as notifications_v2
)
app.include_router(health_v2.router, tags=["Health & Monitoring v2"])
app.include_router(metrics_v2.router, tags=["Metrics & Analytics v2"])
app.include_router(jobs_v2.router, tags=["Jobs Management v2"])
app.include_router(templates_v2.router, tags=["Templates Management v2"])
app.include_router(system_v2.router, tags=["System Administration v2"])
app.include_router(discovery_v2.router, tags=["Network Discovery v2"])
app.include_router(notifications_v2.router, tags=["Notifications & Alerts v2"])

@app.get("/")
async def root():
    return {
        "message": "OpsConductor Universal Automation Orchestration Platform",
        "version": "1.0.0",
        "status": "running"
    }

# Legacy health endpoints removed - use /api/v2/health/ instead

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 