"""
Monitoring API v1 for system metrics and observability.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database.database import get_db
from app.models.user_models import User
from app.domains.monitoring.services.metrics_service import MetricsService
from app.core.security import verify_token
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/monitoring")
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Get metrics service with dependencies."""
    return MetricsService(db)


@router.get("/metrics")
async def get_system_metrics(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive system metrics."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view system metrics"
        )
    
    metrics = await service.get_system_metrics()
    return metrics


@router.get("/health")
async def get_health_score(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Get system health score."""
    health = await service.get_health_score()
    return health


@router.get("/health/public")
async def get_health_score_public(
    service: MetricsService = Depends(get_metrics_service)
):
    """Get system health score (public endpoint for monitoring)."""
    health = await service.get_health_score()
    return health


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """Get metrics in Prometheus format."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access Prometheus metrics"
        )
    
    metrics_text = await service.get_prometheus_metrics()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/metrics/prometheus/public")
async def get_prometheus_metrics_public(
    service: MetricsService = Depends(get_metrics_service)
):
    """Get metrics in Prometheus format (public endpoint for monitoring)."""
    metrics_text = await service.get_prometheus_metrics()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/status")
async def get_system_status(
    service: MetricsService = Depends(get_metrics_service)
):
    """Get basic system status (public endpoint)."""
    try:
        health = await service.get_health_score()
        return {
            "status": "healthy" if health["health_score"] > 50 else "unhealthy",
            "health_score": health["health_score"],
            "timestamp": health["timestamp"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "health_score": 0
        }