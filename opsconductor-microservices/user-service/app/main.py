"""
User Service - Main Application
Independent microservice for user management in OpsConductor
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.core.events import event_publisher
from app.api.v1 import users, roles, permissions, profiles, health
from opsconductor_shared.models.base import ServiceType, EventType

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting User Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize event publisher
    if event_publisher:
        try:
            # Publish service started event
            await event_publisher.publish_event(
                event_type=EventType.SERVICE_STARTED,
                service_name=ServiceType.USER_SERVICE,
                data={
                    "service_name": "user-service",
                    "version": "1.0.0",
                    "environment": settings.ENVIRONMENT
                }
            )
            logger.info("Service started event published")
        except Exception as e:
            logger.warning(f"Failed to publish service started event: {e}")
    
    logger.info("User Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down User Service...")
    
    # Publish service stopped event
    if event_publisher:
        try:
            await event_publisher.publish_event(
                event_type=EventType.SERVICE_STOPPED,
                service_name=ServiceType.USER_SERVICE,
                data={
                    "service_name": "user-service",
                    "shutdown_reason": "normal"
                }
            )
            logger.info("Service stopped event published")
        except Exception as e:
            logger.warning(f"Failed to publish service stopped event: {e}")
    
    logger.info("User Service stopped")


# Create FastAPI application
app = FastAPI(
    title="User Service",
    description="Independent microservice for user management in OpsConductor",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Publish error event
    if event_publisher:
        try:
            await event_publisher.publish_event(
                event_type=EventType.SERVICE_ERROR,
                service_name=ServiceType.USER_SERVICE,
                data={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "endpoint": str(request.url),
                    "method": request.method
                }
            )
        except Exception as e:
            logger.warning(f"Failed to publish error event: {e}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "service": "user-service",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "user-service",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )