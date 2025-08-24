"""
Job Service - Main Application
Independent microservice for job management and execution in OpsConductor
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
from app.api.v1 import jobs, executions, schedules, health
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
    logger.info("Starting Job Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Removed: event publisher initialization - Using direct HTTP communication
    logger.info("Job Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Job Service...")
    
    # Removed: service stopped event - Using direct HTTP communication
    logger.info("Job Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Job Service",
    description="Independent microservice for job management and execution in OpsConductor",
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
    
    # Log error details
    logger.error(f"Error on {request.method} {request.url}: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "service": "job-service",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(executions.router, prefix="/api/v1/executions", tags=["Executions"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["Schedules"])


# Service info endpoint - standardized location
@app.get("/api/v1/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "job-service",
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