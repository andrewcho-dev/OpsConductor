"""
Job Management Service - Main Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import create_tables
from app.api import jobs
from opsconductor_shared.events.subscriber import EventSubscriber
from opsconductor_shared.models.base import EventType, BaseEvent

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Event handlers
def handle_execution_completed(event: BaseEvent):
    """Handle execution completed events"""
    logger.info(f"Received execution completed event: {event.data}")
    # TODO: Update job status based on execution result


def handle_execution_failed(event: BaseEvent):
    """Handle execution failed events"""
    logger.info(f"Received execution failed event: {event.data}")
    # TODO: Update job status to failed


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
    
    # Setup event subscriber
    try:
        event_subscriber = EventSubscriber("job-management", settings.rabbitmq_url)
        
        # Subscribe to execution events
        event_subscriber.subscribe(
            [EventType.EXECUTION_COMPLETED, EventType.EXECUTION_FAILED],
            handle_execution_completed
        )
        
        # Start consuming events in background
        event_subscriber.start_consuming_async()
        logger.info("✅ Event subscriber started")
        
    except Exception as e:
        logger.error(f"❌ Failed to setup event subscriber: {e}")
        # Don't fail startup if events are not available
    
    yield
    
    # Shutdown
    logger.info(f"🛑 Shutting down {settings.service_name}")


# Create FastAPI application
app = FastAPI(
    title="Job Management Service",
    description="Microservice for job definition and lifecycle management",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
            "service": settings.service_name
        }
    )


# Include API routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
    }


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
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )