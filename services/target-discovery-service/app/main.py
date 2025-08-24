"""
Target Discovery Service - Main Application
Independent microservice for network discovery and target identification in OpsConductor
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
# Removed: event_publisher - Using direct HTTP communication
from app.api.v1 import discovery, devices, templates, health
# Removed: ServiceType, EventType - Using direct HTTP communication

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
    logger.info("Starting Target Discovery Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize event publisher
    if event_publisher:
        try:
            # Publish service started event
            await event_publisher.publish_event(
                event_type=EventType.SERVICE_STARTED,
                service_name=ServiceType.TARGET_DISCOVERY_SERVICE,
                data={
                    "service_name": "target-discovery-service",
                    "version": "1.0.0",
                    "environment": settings.ENVIRONMENT
                }
            )
            logger.info("Service started event published")
        except Exception as e:
            logger.warning(f"Failed to publish service started event: {e}")
    
    logger.info("Target Discovery Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Target Discovery Service...")
    
    # Publish service stopped event
    if event_publisher:
        try:
            await event_publisher.publish_event(
                event_type=EventType.SERVICE_STOPPED,
                service_name=ServiceType.TARGET_DISCOVERY_SERVICE,
                data={
                    "service_name": "target-discovery-service",
                    "shutdown_reason": "normal"
                }
            )
            logger.info("Service stopped event published")
        except Exception as e:
            logger.warning(f"Failed to publish service stopped event: {e}")
    
    logger.info("Target Discovery Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Target Discovery Service",
    description="Independent microservice for network discovery and target identification in OpsConductor",
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
                service_name=ServiceType.TARGET_DISCOVERY_SERVICE,
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
            "service": "target-discovery-service",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["Discovery"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])


# Service info endpoint - standardized location
@app.get("/api/v1/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "target-discovery-service",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )