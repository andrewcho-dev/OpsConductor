"""
Health check endpoints for Target Discovery Service
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.core.database import get_db
from app.core.config import settings
from app.models.discovery import DiscoveryJob, DiscoveredDevice

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "target-discovery-service",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "target-discovery-service",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": {
                    "database": "unhealthy"
                }
            }
        )


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with comprehensive system status
    """
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check discovery_jobs table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM discovery_jobs"))
        job_count = result.scalar()
        checks["discovery_jobs_table"] = {
            "status": "healthy",
            "message": f"Discovery jobs table accessible, {job_count} jobs stored"
        }
    except Exception as e:
        checks["discovery_jobs_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access discovery jobs table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check discovered_devices table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM discovered_devices"))
        device_count = result.scalar()
        checks["discovered_devices_table"] = {
            "status": "healthy",
            "message": f"Discovered devices table accessible, {device_count} devices stored"
        }
    except Exception as e:
        checks["discovered_devices_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access discovered devices table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check recent discovery activity
    try:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_jobs = db.query(DiscoveryJob).filter(
            DiscoveryJob.created_at >= one_hour_ago
        ).count()
        
        checks["recent_activity"] = {
            "status": "healthy",
            "message": f"{recent_jobs} discovery jobs created in the last hour"
        }
    except Exception as e:
        checks["recent_activity"] = {
            "status": "unhealthy",
            "message": f"Cannot check recent discovery activity: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Redis check (if configured)
    if settings.REDIS_URL:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            checks["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            checks["redis"] = {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}"
            }
            # Redis failure doesn't make the service unhealthy
    
    # Discovery statistics
    discovery_stats = {}
    try:
        # Jobs by status
        job_stats = db.query(
            DiscoveryJob.status,
            func.count(DiscoveryJob.id).label('count')
        ).group_by(DiscoveryJob.status).all()
        
        # Devices discovered in last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        devices_24h = db.query(DiscoveredDevice).filter(
            DiscoveredDevice.discovered_at >= twenty_four_hours_ago
        ).count()
        
        discovery_stats = {
            "jobs_by_status": {status: count for status, count in job_stats},
            "devices_discovered_24h": devices_24h,
            "total_jobs": db.query(DiscoveryJob).count(),
            "total_devices": db.query(DiscoveredDevice).count()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery stats: {e}")
        discovery_stats = {"error": str(e)}
    
    response = {
        "status": overall_status,
        "service": "target-discovery-service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "discovery_stats": discovery_stats
    }
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - determines if service is ready to accept requests
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        # Check if essential tables exist
        db.execute(text("SELECT 1 FROM discovery_jobs LIMIT 1"))
        db.execute(text("SELECT 1 FROM discovered_devices LIMIT 1"))
        
        return {
            "ready": True,
            "service": "target-discovery-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "service": "target-discovery-service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check - determines if service is alive
    """
    return {
        "alive": True,
        "service": "target-discovery-service",
        "timestamp": datetime.utcnow().isoformat()
    }