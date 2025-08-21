"""
User Service Main Application
"""
import logging
from datetime import datetime
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.database.database import create_tables, test_connection
from app.api import users
from app.schemas.user import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OpsConductor User Service",
    description="User management microservice for OpsConductor platform",
    version=settings.SERVICE_VERSION,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# PROMETHEUS METRICS INSTRUMENTATION
# =============================================================================
# Initialize Prometheus instrumentator with basic configuration
instrumentator = Instrumentator()
instrumentator.instrument(app)

# Include routers
app.include_router(users.router)


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}...")
    
    # Test database connection
    if test_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        raise Exception("Cannot connect to database")
    
    # Create tables (mainly for development)
    create_tables()
    logger.info("Database tables created/verified")
    
    logger.info(f"{settings.SERVICE_NAME} startup complete")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db_status = "healthy" if test_connection() else "unhealthy"
    
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        database=db_status,
        timestamp=datetime.now()
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"OpsConductor {settings.SERVICE_NAME}",
        "version": settings.SERVICE_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )