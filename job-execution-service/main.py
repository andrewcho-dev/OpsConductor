"""
Job Execution Service - Main Application
FastAPI application for job orchestration and execution
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import create_tables
from app.api import jobs, executions, schedules, system


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"🚀 Starting {settings.service_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Create database tables
    try:
        create_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise
    
    # Log service configuration
    logger.info(f"🔧 Max concurrent targets: {settings.max_concurrent_targets}")
    logger.info(f"🔧 Connection timeout: {settings.connection_timeout}s")
    logger.info(f"🔧 Command timeout: {settings.command_timeout}s")
    logger.info(f"🔧 Retry enabled: {settings.enable_retry}")
    if settings.enable_retry:
        logger.info(f"🔧 Max retries: {settings.max_retries}")
        logger.info(f"🔧 Retry backoff base: {settings.retry_backoff_base}")
    
    yield
    
    # Shutdown
    logger.info(f"🛑 Shutting down {settings.service_name}")


# Create FastAPI application
app = FastAPI(
    title="Job Execution Service",
    description="Microservice for job orchestration, execution, and scheduling",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
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
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# Include API routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(executions.router, prefix="/api/v1/executions", tags=["Executions"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["Schedules"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )