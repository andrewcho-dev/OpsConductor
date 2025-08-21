"""
Notification Service - Main Application
Independent microservice for notifications and alerts in OpsConductor
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
from app.core.events import event_consumer
from app.api.v1 import notifications, templates, alerts, health
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
    logger.info("Starting Notification Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Start event consumer for notification triggers
    if event_consumer:
        try:
            await event_consumer.start_consuming()
            logger.info("Event consumer started")
        except Exception as e:
            logger.warning(f"Failed to start event consumer: {e}")
    
    logger.info("Notification Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Notification Service...")
    
    # Stop event consumer
    if event_consumer:
        try:
            await event_consumer.stop_consuming()
            logger.info("Event consumer stopped")
        except Exception as e:
            logger.warning(f"Failed to stop event consumer: {e}")
    
    logger.info("Notification Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Notification Service",
    description="Independent microservice for notifications and alerts in OpsConductor",
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
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "service": "notification-service",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])


# Service info endpoint - standardized location
@app.get("/api/v1/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "notification-service",
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