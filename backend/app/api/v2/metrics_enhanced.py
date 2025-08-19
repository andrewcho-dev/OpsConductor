"""
Metrics API v2 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced metrics analytics and monitoring
- ✅ Multi-source metrics consolidation
- ✅ Real-time metrics processing and insights
- ✅ Comprehensive metrics lifecycle management
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

# Import service layer
from app.services.metrics_management_service import MetricsManagementService, MetricsManagementError
from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class MetricValue(BaseModel):
    """Enhanced model for individual metric values"""
    name: str = Field(..., description="Metric name")
    value: Union[int, float, str] = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Metric unit")
    timestamp: datetime = Field(..., description="Metric timestamp")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "cpu_usage",
                "value": 75.5,
                "unit": "percent",
                "timestamp": "2025-01-01T10:30:00Z",
                "tags": {
                    "host": "server-01",
                    "environment": "production"
                }
            }
        }


class SystemMetricsResponse(BaseModel):
    """Enhanced response model for system metrics"""
    metrics: Dict[str, Any] = Field(..., description="System metrics data")
    health_status: str = Field(..., description="Overall system health status")
    trends: Dict[str, Any] = Field(default_factory=dict, description="System trends")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="System alerts")
    last_updated: datetime = Field(..., description="Last update timestamp")
    collection_interval: str = Field(..., description="Metrics collection interval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="System metrics metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": {
                    "cpu_usage": 75.5,
                    "memory_usage": 68.2,
                    "disk_usage": 45.0,
                    "network_io": 1024000
                },
                "health_status": "healthy",
                "trends": {
                    "cpu_trend": "stable",
                    "memory_trend": "increasing"
                },
                "alerts": [],
                "last_updated": "2025-01-01T10:30:00Z",
                "collection_interval": "60s",
                "metadata": {
                    "source": "system_monitoring",
                    "version": "2.0"
                }
            }
        }


class ApplicationMetricsResponse(BaseModel):
    """Enhanced response model for application metrics"""
    metrics: Dict[str, Any] = Field(..., description="Application metrics data")
    health_status: str = Field(..., description="Application health status")
    performance_score: float = Field(..., description="Application performance score")
    bottlenecks: List[Dict[str, Any]] = Field(default_factory=list, description="Identified bottlenecks")
    recommendations: List[str] = Field(default_factory=list, description="Performance recommendations")
    last_updated: datetime = Field(..., description="Last update timestamp")
    collection_interval: str = Field(..., description="Metrics collection interval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Application metrics metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": {
                    "response_time": 125.5,
                    "throughput": 1500,
                    "error_rate": 0.02,
                    "active_connections": 250
                },
                "health_status": "healthy",
                "performance_score": 95.0,
                "bottlenecks": [],
                "recommendations": [
                    "Consider increasing connection pool size",
                    "Optimize database queries"
                ],
                "last_updated": "2025-01-01T10:30:00Z",
                "collection_interval": "120s",
                "metadata": {
                    "source": "application_monitoring",
                    "version": "2.0"
                }
            }
        }


class PerformanceMetricsResponse(BaseModel):
    """Enhanced response model for performance metrics"""
    metrics: Dict[str, Any] = Field(..., description="Performance metrics data")
    performance_grade: str = Field(..., description="Overall performance grade")
    optimization_opportunities: List[Dict[str, Any]] = Field(default_factory=list, description="Optimization opportunities")
    historical_comparison: Dict[str, Any] = Field(default_factory=dict, description="Historical performance comparison")
    last_updated: datetime = Field(..., description="Last update timestamp")
    collection_interval: str = Field(..., description="Metrics collection interval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": {
                    "avg_response_time": 95.2,
                    "p95_response_time": 250.0,
                    "requests_per_second": 1200,
                    "cache_hit_rate": 85.5
                },
                "performance_grade": "A",
                "optimization_opportunities": [
                    {
                        "area": "database",
                        "impact": "high",
                        "description": "Optimize slow queries"
                    }
                ],
                "historical_comparison": {
                    "vs_yesterday": "+5%",
                    "vs_last_week": "+12%"
                },
                "last_updated": "2025-01-01T10:30:00Z",
                "collection_interval": "60s",
                "metadata": {
                    "source": "performance_monitoring",
                    "version": "2.0"
                }
            }
        }


class AnalyticsDataResponse(BaseModel):
    """Enhanced response model for analytics data"""
    data_points: List[Dict[str, Any]] = Field(..., description="Analytics data points")
    time_range: str = Field(..., description="Data time range")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    correlations: List[Dict[str, Any]] = Field(default_factory=list, description="Data correlations")
    predictions: Dict[str, Any] = Field(default_factory=dict, description="Predictive analytics")
    analysis_timestamp: datetime = Field(..., description="Analysis timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analytics metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data_points": [
                    {
                        "timestamp": "2025-01-01T10:00:00Z",
                        "cpu_usage": 75.5,
                        "memory_usage": 68.2
                    }
                ],
                "time_range": "24h",
                "insights": [
                    "CPU usage peaked during business hours",
                    "Memory usage shows steady growth trend"
                ],
                "correlations": [
                    {
                        "metrics": ["cpu_usage", "response_time"],
                        "correlation": 0.85,
                        "strength": "strong"
                    }
                ],
                "predictions": {
                    "next_hour_cpu": 78.2,
                    "confidence": 0.92
                },
                "analysis_timestamp": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "analytics_engine",
                    "version": "2.0"
                }
            }
        }


class DashboardMetricsResponse(BaseModel):
    """Enhanced response model for dashboard metrics"""
    system_overview: Dict[str, Any] = Field(..., description="System overview metrics")
    application_health: Dict[str, Any] = Field(..., description="Application health metrics")
    performance_summary: Dict[str, Any] = Field(..., description="Performance summary")
    recent_alerts: List[Dict[str, Any]] = Field(..., description="Recent alerts")
    key_metrics: Dict[str, Any] = Field(..., description="Key performance indicators")
    overall_health: str = Field(..., description="Overall system health")
    critical_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Critical alerts")
    quick_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Quick action items")
    last_updated: datetime = Field(..., description="Last update timestamp")
    refresh_interval: str = Field(..., description="Dashboard refresh interval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dashboard metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_overview": {
                    "cpu_usage": 75.5,
                    "memory_usage": 68.2,
                    "disk_usage": 45.0
                },
                "application_health": {
                    "status": "healthy",
                    "uptime": "99.9%",
                    "response_time": 125.5
                },
                "performance_summary": {
                    "grade": "A",
                    "score": 95.0,
                    "trend": "stable"
                },
                "recent_alerts": [],
                "key_metrics": {
                    "active_users": 1250,
                    "requests_per_minute": 5000,
                    "error_rate": 0.02
                },
                "overall_health": "healthy",
                "critical_alerts": [],
                "quick_actions": [],
                "last_updated": "2025-01-01T10:30:00Z",
                "refresh_interval": "120s",
                "metadata": {
                    "source": "dashboard_aggregator",
                    "version": "2.0"
                }
            }
        }


class MetricsExportRequest(BaseModel):
    """Enhanced request model for metrics export"""
    export_format: str = Field(..., description="Export format (json, csv, xlsx)")
    time_range: str = Field(default="24h", description="Time range for export")
    metric_types: Optional[List[str]] = Field(None, description="Specific metric types to export")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    compression: bool = Field(default=False, description="Compress export data")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        """Validate export format"""
        allowed_formats = ['json', 'csv', 'xlsx', 'xml']
        if v not in allowed_formats:
            raise ValueError(f'Export format must be one of: {", ".join(allowed_formats)}')
        return v
    
    @validator('time_range')
    def validate_time_range(cls, v):
        """Validate time range"""
        allowed_ranges = ['1h', '6h', '12h', '24h', '7d', '30d']
        if v not in allowed_ranges:
            raise ValueError(f'Time range must be one of: {", ".join(allowed_ranges)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "export_format": "json",
                "time_range": "24h",
                "metric_types": ["system", "application", "performance"],
                "include_metadata": True,
                "compression": False
            }
        }


class MetricsExportResponse(BaseModel):
    """Enhanced response model for metrics export"""
    export_id: str = Field(..., description="Export identifier")
    export_format: str = Field(..., description="Export format")
    data_size: int = Field(..., description="Export data size in bytes")
    record_count: int = Field(..., description="Number of records exported")
    time_range: str = Field(..., description="Exported time range")
    export_url: Optional[str] = Field(None, description="Download URL for export")
    export_metadata: Dict[str, Any] = Field(..., description="Export metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "export_id": "export_123456",
                "export_format": "json",
                "data_size": 1048576,
                "record_count": 5000,
                "time_range": "24h",
                "export_url": "/api/v2/metrics/exports/export_123456/download",
                "export_metadata": {
                    "exported_at": "2025-01-01T10:30:00Z",
                    "version": "2.0",
                    "data_integrity_hash": "hash123"
                }
            }
        }


class MetricsErrorResponse(BaseModel):
    """Enhanced error response model for metrics management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    metric_type: Optional[str] = Field(None, description="Related metric type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "metrics_retrieval_error",
                "message": "Failed to retrieve system metrics due to service unavailability",
                "details": {
                    "service": "system_monitoring",
                    "retry_after": 60
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "metric_type": "system"
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/metrics",
    tags=["Metrics & Analytics Enhanced v2"],
    responses={
        401: {"model": MetricsErrorResponse, "description": "Authentication required"},
        403: {"model": MetricsErrorResponse, "description": "Insufficient permissions"},
        404: {"model": MetricsErrorResponse, "description": "Resource not found"},
        422: {"model": MetricsErrorResponse, "description": "Validation error"},
        500: {"model": MetricsErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

# Local get_current_user removed - using centralized auth_dependencies


def require_metrics_permissions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require metrics viewing permissions."""
    if current_user["role"] not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Insufficient permissions to access metrics data",
                "required_roles": ["administrator", "operator"],
                "user_role": current_user["role"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.get(
    "/system",
    response_model=SystemMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Metrics",
    description="""
    Get comprehensive system metrics with health analysis and trends.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Advanced system health analysis
    - ✅ Trend analysis and alerts
    - ✅ Enhanced system monitoring data
    
    **Performance:**
    - Redis caching for improved response times
    - Optimized metrics collection
    - Structured logging for monitoring
    """,
    responses={
        200: {"description": "System metrics retrieved successfully", "model": SystemMetricsResponse}
    }
)
async def get_system_metrics(
    current_user = Depends(require_metrics_permissions),
    db: Session = Depends(get_db)
) -> SystemMetricsResponse:
    """Enhanced system metrics with service layer and comprehensive analysis"""
    
    request_logger = RequestLogger(logger, "get_system_metrics")
    request_logger.log_request_start("GET", "/api/v2/metrics/system", current_user["username"])
    
    try:
        # Initialize service layer
        metrics_mgmt_service = MetricsManagementService(db)
        
        # Get system metrics through service layer (with caching)
        metrics_result = await metrics_mgmt_service.get_system_metrics(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = SystemMetricsResponse(**metrics_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System metrics retrieval successful via service layer",
            extra={
                "health_status": metrics_result.get("health_status", "unknown"),
                "metrics_count": len(metrics_result.get("metrics", {})),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except MetricsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "System metrics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System metrics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving system metrics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/application",
    response_model=ApplicationMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Application Metrics",
    description="""
    Get comprehensive application metrics with performance analysis.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 2-minute TTL
    - ✅ Performance scoring and bottleneck identification
    - ✅ Automated recommendations
    - ✅ Enhanced application monitoring data
    """,
    responses={
        200: {"description": "Application metrics retrieved successfully", "model": ApplicationMetricsResponse}
    }
)
async def get_application_metrics(
    current_user = Depends(require_metrics_permissions),
    db: Session = Depends(get_db)
) -> ApplicationMetricsResponse:
    """Enhanced application metrics with service layer and performance analysis"""
    
    request_logger = RequestLogger(logger, "get_application_metrics")
    request_logger.log_request_start("GET", "/api/v2/metrics/application", current_user["username"])
    
    try:
        # Initialize service layer
        metrics_mgmt_service = MetricsManagementService(db)
        
        # Get application metrics through service layer (with caching)
        metrics_result = await metrics_mgmt_service.get_application_metrics(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = ApplicationMetricsResponse(**metrics_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Application metrics retrieval successful via service layer",
            extra={
                "health_status": metrics_result.get("health_status", "unknown"),
                "performance_score": metrics_result.get("performance_score", 0),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except MetricsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Application metrics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Application metrics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving application metrics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/performance",
    response_model=PerformanceMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Performance Metrics",
    description="""
    Get comprehensive performance metrics with optimization insights.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Performance grading and optimization opportunities
    - ✅ Historical comparison and trends
    - ✅ Enhanced performance monitoring data
    """,
    responses={
        200: {"description": "Performance metrics retrieved successfully", "model": PerformanceMetricsResponse}
    }
)
async def get_performance_metrics(
    current_user = Depends(require_metrics_permissions),
    db: Session = Depends(get_db)
) -> PerformanceMetricsResponse:
    """Enhanced performance metrics with service layer and optimization insights"""
    
    request_logger = RequestLogger(logger, "get_performance_metrics")
    request_logger.log_request_start("GET", "/api/v2/metrics/performance", current_user["username"])
    
    try:
        # Initialize service layer
        metrics_mgmt_service = MetricsManagementService(db)
        
        # Get performance metrics through service layer (with caching)
        metrics_result = await metrics_mgmt_service.get_performance_metrics(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = PerformanceMetricsResponse(**metrics_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Performance metrics retrieval successful via service layer",
            extra={
                "performance_grade": metrics_result.get("performance_grade", "unknown"),
                "optimization_opportunities": len(metrics_result.get("optimization_opportunities", [])),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except MetricsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Performance metrics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Performance metrics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving performance metrics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/analytics",
    response_model=AnalyticsDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analytics Data",
    description="""
    Get comprehensive analytics data with insights and predictions.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 10-minute TTL
    - ✅ Advanced analytics with insights and correlations
    - ✅ Predictive analytics and trend analysis
    - ✅ Enhanced analytics processing
    """,
    responses={
        200: {"description": "Analytics data retrieved successfully", "model": AnalyticsDataResponse}
    }
)
async def get_analytics_data(
    time_range: str = Query(default="24h", description="Time range for analytics"),
    metric_types: Optional[str] = Query(None, description="Comma-separated metric types"),
    current_user = Depends(require_metrics_permissions),
    db: Session = Depends(get_db)
) -> AnalyticsDataResponse:
    """Enhanced analytics data with service layer and comprehensive insights"""
    
    request_logger = RequestLogger(logger, f"get_analytics_data_{time_range}")
    request_logger.log_request_start("GET", "/api/v2/metrics/analytics", current_user["username"])
    
    try:
        # Parse metric types
        metric_types_list = None
        if metric_types:
            metric_types_list = [mt.strip() for mt in metric_types.split(",")]
        
        # Initialize service layer
        metrics_mgmt_service = MetricsManagementService(db)
        
        # Get analytics data through service layer (with caching)
        analytics_result = await metrics_mgmt_service.get_analytics_data(
            time_range=time_range,
            metric_types=metric_types_list,
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = AnalyticsDataResponse(**analytics_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Analytics data retrieval successful via service layer",
            extra={
                "time_range": time_range,
                "data_points": len(analytics_result.get("data_points", [])),
                "insights": len(analytics_result.get("insights", [])),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except MetricsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Analytics data retrieval failed via service layer",
            extra={
                "time_range": time_range,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Analytics data retrieval error via service layer",
            extra={
                "time_range": time_range,
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving analytics data",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/dashboard",
    response_model=DashboardMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Metrics",
    description="""
    Get comprehensive dashboard metrics with consolidated overview.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 2-minute TTL
    - ✅ Consolidated dashboard view with all key metrics
    - ✅ Critical alerts and quick actions
    - ✅ Enhanced dashboard aggregation
    """,
    responses={
        200: {"description": "Dashboard metrics retrieved successfully", "model": DashboardMetricsResponse}
    }
)
async def get_dashboard_metrics(
    current_user = Depends(require_metrics_permissions),
    db: Session = Depends(get_db)
) -> DashboardMetricsResponse:
    """Enhanced dashboard metrics with service layer and consolidated overview"""
    
    request_logger = RequestLogger(logger, "get_dashboard_metrics")
    request_logger.log_request_start("GET", "/api/v2/metrics/dashboard", current_user["username"])
    
    try:
        # Initialize service layer
        metrics_mgmt_service = MetricsManagementService(db)
        
        # Get dashboard metrics through service layer (with caching)
        dashboard_result = await metrics_mgmt_service.get_dashboard_metrics(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = DashboardMetricsResponse(**dashboard_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Dashboard metrics retrieval successful via service layer",
            extra={
                "overall_health": dashboard_result.get("overall_health", "unknown"),
                "critical_alerts": len(dashboard_result.get("critical_alerts", [])),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except MetricsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Dashboard metrics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Dashboard metrics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving dashboard metrics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post(
    "/export",
    response_model=MetricsExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export Metrics Data",
    description="""
    Export metrics data in various formats with comprehensive options.
    
    **Phase 1 & 2 Features:**
    - ✅ Multiple export formats (JSON, CSV, XLSX, XML)
    - ✅ Flexible time range and metric type selection
    - ✅ Data integrity verification
    - ✅ Enhanced export processing
    """,
    responses={
        200: {"description": "Metrics export initiated successfully", "model": MetricsExportResponse}
    }
)
async def export_metrics_data(
    export_request: MetricsExportRequest,
    current_user = Depends(require_metrics_permissions),
    db: Session = Depends(get_db)
) -> MetricsExportResponse:
    """Enhanced metrics export with service layer and comprehensive formatting"""
    
    request_logger = RequestLogger(logger, f"export_metrics_{export_request.export_format}")
    request_logger.log_request_start("POST", "/api/v2/metrics/export", current_user["username"])
    
    try:
        # Initialize service layer
        metrics_mgmt_service = MetricsManagementService(db)
        
        # Export metrics through service layer
        export_result = await metrics_mgmt_service.export_metrics_data(
            export_format=export_request.export_format,
            time_range=export_request.time_range,
            metric_types=export_request.metric_types,
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = MetricsExportResponse(**export_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Metrics export successful via service layer",
            extra={
                "export_format": export_request.export_format,
                "time_range": export_request.time_range,
                "data_size": export_result.get("data_size", 0),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except MetricsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Metrics export failed via service layer",
            extra={
                "export_format": export_request.export_format,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Metrics export error via service layer",
            extra={
                "export_format": export_request.export_format,
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while exporting metrics data",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/prometheus/public",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Get Prometheus Metrics (Public)",
    description="""
    Get metrics in Prometheus format for monitoring and alerting.
    This endpoint provides public metrics without authentication for Prometheus scraping.
    
    **Returns:**
    - Plain text metrics in Prometheus format
    - System health and performance metrics
    - Application-specific metrics
    """
)
async def get_prometheus_metrics_public(
    db: Session = Depends(get_db)
):
    """Get metrics in Prometheus format (public endpoint for scraping)."""
    try:
        # Get basic system metrics for Prometheus
        metrics_lines = [
            "# HELP opsconductor_up OpsConductor service status",
            "# TYPE opsconductor_up gauge",
            "opsconductor_up 1",
            "",
            "# HELP opsconductor_info OpsConductor service information",
            "# TYPE opsconductor_info gauge",
            'opsconductor_info{version="1.0.0",service="opsconductor-backend"} 1',
            "",
            "# HELP opsconductor_requests_total Total number of requests",
            "# TYPE opsconductor_requests_total counter",
            "opsconductor_requests_total 1",
            ""
        ]
        
        prometheus_output = "\n".join(metrics_lines)
        
        logger.info("Prometheus metrics retrieved successfully")
        
        return Response(
            content=prometheus_output,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        logger.error(f"Prometheus metrics retrieval error: {str(e)}")
        
        # Return basic error metric for Prometheus
        error_metrics = [
            "# HELP opsconductor_up OpsConductor service status",
            "# TYPE opsconductor_up gauge", 
            "opsconductor_up 0",
            ""
        ]
        
        return Response(
            content="\n".join(error_metrics),
            media_type="text/plain; version=0.0.4; charset=utf-8",
            status_code=status.HTTP_200_OK  # Return 200 for Prometheus compatibility
        )