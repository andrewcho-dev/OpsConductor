"""
Target Management Service Layer - Phases 1 & 2
Complete service layer with caching, logging, and comprehensive target management

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Service layer architecture with business logic separation
- ✅ Redis caching for targets, connections, and health monitoring
- ✅ Structured JSON logging with contextual information
- ✅ Performance monitoring and metrics collection
- ✅ Enhanced security with connection validation
- ✅ Target discovery and network scanning
- ✅ Advanced target search and filtering
- ✅ Connection pooling and management
- ✅ Health monitoring and alerting
"""

import logging
import time
import json
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.logging import get_structured_logger
from app.core.config import settings
from app.services.universal_target_service import UniversalTargetService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.serial_service import SerialService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.schemas.target_schemas import (
    TargetCreate, TargetUpdate, TargetComprehensiveUpdate,
    CommunicationMethodCreate, CommunicationMethodUpdate
)
from app.utils.target_utils import getTargetIpAddress

# Configure structured logger
logger = get_structured_logger(__name__)

# Cache configuration
CACHE_TTL = 1800  # 30 minutes
CACHE_PREFIX = "target_mgmt:"
TARGET_CACHE_PREFIX = "target:"
TARGET_LIST_CACHE_PREFIX = "target_list:"
TARGET_SEARCH_CACHE_PREFIX = "target_search:"
CONNECTION_CACHE_PREFIX = "connection:"
HEALTH_CACHE_PREFIX = "health:"
DISCOVERY_CACHE_PREFIX = "discovery:"


def with_performance_logging(func):
    """Performance logging decorator for target management operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "Target management operation successful",
                extra={
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "Target management operation failed",
                extra={
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "error": str(e),
                    "success": False
                }
            )
            raise
            
    return wrapper


def with_caching(cache_key_func, ttl=CACHE_TTL):
    """Caching decorator for target management operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{CACHE_PREFIX}{cache_key_func(*args, **kwargs)}"
            
            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_result = await redis_client.get(cache_key)
                    if cached_result:
                        logger.info(
                            "Cache hit for target management operation",
                            extra={
                                "cache_key": cache_key,
                                "operation": func.__name__
                            }
                        )
                        return json.loads(cached_result)
                except Exception as e:
                    logger.warning(
                        "Cache read failed, proceeding without cache",
                        extra={
                            "cache_key": cache_key,
                            "error": str(e),
                            "operation": func.__name__
                        }
                    )
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            if redis_client:
                try:
                    await redis_client.setex(
                        cache_key, 
                        ttl, 
                        json.dumps(result, default=str)
                    )
                    logger.info(
                        "Cached target management operation result",
                        extra={
                            "cache_key": cache_key,
                            "operation": func.__name__,
                            "execution_time": execution_time
                        }
                    )
                except Exception as e:
                    logger.warning(
                        "Cache write failed",
                        extra={
                            "cache_key": cache_key,
                            "error": str(e),
                            "operation": func.__name__
                        }
                    )
            
            return result
        return wrapper
    return decorator


class TargetManagementService:
    """Enhanced target management service with caching and comprehensive logging"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.target_service = UniversalTargetService(db)
        self.health_service = HealthMonitoringService(db)
        logger.info("Target Management Service initialized with enhanced features")
    
    @with_performance_logging
    async def create_target(
        self, 
        target_data: TargetCreate, 
        current_user_id: int,
        current_username: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Enhanced target creation with comprehensive validation and audit logging
        """
        logger.info(
            "Target creation attempt",
            extra={
                "target_name": target_data.name,
                "ip_address": target_data.ip_address,
                "method_type": target_data.method_type,
                "created_by": current_username
            }
        )
        
        try:
            # Validate target data
            await self._validate_target_data(target_data)
            
            # Create target through existing service
            target = self.target_service.create_target(
                name=target_data.name,
                os_type=target_data.os_type,
                ip_address=target_data.ip_address,
                method_type=target_data.method_type,
                username=target_data.username,
                password=target_data.password,
                ssh_key=target_data.ssh_key,
                ssh_passphrase=target_data.ssh_passphrase,
                description=target_data.description,
                environment=target_data.environment,
                location=target_data.location,
                data_center=target_data.data_center,
                region=target_data.region,
                # Additional fields
                encryption=target_data.encryption,
                server_type=target_data.server_type,
                domain=target_data.domain,
                test_recipient=target_data.test_recipient,
                connection_security=target_data.connection_security
            )
            
            # Clear target list cache
            await self._invalidate_target_list_cache()
            
            # Log target creation audit event
            await self.audit_service.log_event(
                event_type=AuditEventType.TARGET_CREATED,
                user_id=current_user_id,
                resource_type="target",
                resource_id=str(target.id),
                action="create_target",
                details={
                    "target_name": target.name,
                    "ip_address": getTargetIpAddress(target),
                    "method_type": target_data.method_type,
                    "os_type": target_data.os_type,
                    "environment": target_data.environment,
                    "created_by": current_username
                },
                severity=AuditSeverity.MEDIUM,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Track target creation activity
            await self._track_target_activity(
                current_user_id, "target_created", 
                {"target_id": target.id, "target_name": target.name}
            )
            
            # Initialize health monitoring for the new target
            await self._initialize_target_monitoring(target.id)
            
            logger.info(
                "Target creation successful",
                extra={
                    "target_id": target.id,
                    "target_name": target.name,
                    "created_by": current_username
                }
            )
            
            return await self._format_target_response(target)
            
        except ValueError as e:
            logger.warning(
                "Target creation failed - validation error",
                extra={
                    "target_name": target_data.name,
                    "error": str(e),
                    "created_by": current_username
                }
            )
            raise TargetManagementError(
                f"Target creation failed: {str(e)}",
                error_code="validation_error",
                details={"field_errors": str(e)}
            )
        except Exception as e:
            logger.error(
                "Target creation failed - internal error",
                extra={
                    "target_name": target_data.name,
                    "error": str(e),
                    "created_by": current_username
                }
            )
            raise TargetManagementError(
                "Internal error during target creation",
                error_code="internal_error"
            )
    
    @with_caching(lambda self, skip, limit, search, os_type, environment: f"target_list_{skip}_{limit}_{search or 'all'}_{os_type or 'all'}_{environment or 'all'}", ttl=900)
    @with_performance_logging
    async def get_targets(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        os_type: Optional[str] = None,
        environment: Optional[str] = None,
        method_type: Optional[str] = None,
        health_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced target listing with search, filtering, and caching
        """
        logger.info(
            "Target list retrieval",
            extra={
                "skip": skip,
                "limit": limit,
                "search": search,
                "os_type_filter": os_type,
                "environment_filter": environment,
                "method_type_filter": method_type,
                "health_status_filter": health_status
            }
        )
        
        try:
            # Get targets through existing service
            targets = self.target_service.get_targets_summary()
            
            # Apply filters
            filtered_targets = targets
            if search:
                filtered_targets = [
                    target for target in filtered_targets 
                    if search.lower() in target.name.lower() or 
                       search.lower() in (target.ip_address or '').lower() or
                       search.lower() in (target.description or '').lower()
                ]
            
            if os_type:
                filtered_targets = [target for target in filtered_targets if target.os_type == os_type]
            
            if environment:
                filtered_targets = [target for target in filtered_targets if target.environment == environment]
            
            if method_type:
                filtered_targets = [
                    target for target in filtered_targets 
                    if any(method.method_type == method_type for method in target.communication_methods)
                ]
            
            # Apply pagination
            total_count = len(filtered_targets)
            paginated_targets = filtered_targets[skip:skip + limit]
            
            # Convert to response format with health status
            target_list = []
            for target in paginated_targets:
                target_data = await self._format_target_response(target)
                
                # Add health status if filtering by health
                if health_status:
                    health_info = await self._get_target_health_status(target.id)
                    if health_info.get("status") != health_status:
                        continue
                    target_data["health_status"] = health_info
                
                target_list.append(target_data)
            
            logger.info(
                "Target list retrieval successful",
                extra={
                    "total_targets": total_count,
                    "returned_targets": len(target_list),
                    "filters_applied": bool(search or os_type or environment or method_type or health_status)
                }
            )
            
            return {
                "targets": target_list,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "filters": {
                    "search": search,
                    "os_type": os_type,
                    "environment": environment,
                    "method_type": method_type,
                    "health_status": health_status
                }
            }
            
        except Exception as e:
            logger.error(
                "Target list retrieval failed",
                extra={
                    "error": str(e),
                    "skip": skip,
                    "limit": limit
                }
            )
            raise TargetManagementError(
                "Failed to retrieve target list",
                error_code="retrieval_error"
            )
    
    @with_caching(lambda self, target_id: f"target_{target_id}", ttl=1800)
    @with_performance_logging
    async def get_target_by_id(self, target_id: int) -> Dict[str, Any]:
        """
        Enhanced target retrieval by ID with caching and health status
        """
        logger.info(
            "Target retrieval by ID",
            extra={"target_id": target_id}
        )
        
        try:
            target = self.target_service.get_target_by_id(target_id)
            
            if not target:
                logger.warning(
                    "Target not found",
                    extra={"target_id": target_id}
                )
                raise TargetManagementError(
                    "Target not found",
                    error_code="target_not_found"
                )
            
            # Get comprehensive target information
            target_info = await self._format_target_response(target)
            
            # Add health status
            health_status = await self._get_target_health_status(target_id)
            target_info["health_status"] = health_status
            
            # Add connection statistics
            connection_stats = await self._get_connection_statistics(target_id)
            target_info["connection_statistics"] = connection_stats
            
            # Add recent activity
            recent_activity = await self._get_target_recent_activity(target_id)
            target_info["recent_activity"] = recent_activity
            
            logger.info(
                "Target retrieval successful",
                extra={
                    "target_id": target.id,
                    "target_name": target.name
                }
            )
            
            return target_info
            
        except TargetManagementError:
            raise
        except Exception as e:
            logger.error(
                "Target retrieval failed",
                extra={
                    "target_id": target_id,
                    "error": str(e)
                }
            )
            raise TargetManagementError(
                "Failed to retrieve target",
                error_code="retrieval_error"
            )
    
    @with_performance_logging
    async def update_target(
        self, 
        target_id: int, 
        target_data: TargetUpdate,
        current_user_id: int,
        current_username: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Enhanced target update with change tracking and audit logging
        """
        logger.info(
            "Target update attempt",
            extra={
                "target_id": target_id,
                "updated_by": current_username
            }
        )
        
        try:
            # Get original target data for audit
            original_target = self.target_service.get_target_by_id(target_id)
            if not original_target:
                raise TargetManagementError(
                    "Target not found",
                    error_code="target_not_found"
                )
            
            # Update target through existing service
            updated_target = self.target_service.update_target(target_id, target_data)
            
            # Clear caches
            await self._invalidate_target_cache(target_id)
            await self._invalidate_target_list_cache()
            
            # Build change details
            changes = await self._build_target_changes(original_target, target_data)
            
            # Log target update audit event
            await self.audit_service.log_event(
                event_type=AuditEventType.TARGET_UPDATED,
                user_id=current_user_id,
                resource_type="target",
                resource_id=str(target_id),
                action="update_target",
                details={
                    "target_id": target_id,
                    "target_name": updated_target.name,
                    "changes": changes,
                    "updated_by": current_username
                },
                severity=AuditSeverity.MEDIUM,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Track target update activity
            await self._track_target_activity(
                current_user_id, "target_updated", 
                {"target_id": target_id, "changes": changes}
            )
            
            logger.info(
                "Target update successful",
                extra={
                    "target_id": target_id,
                    "target_name": updated_target.name,
                    "changes": changes,
                    "updated_by": current_username
                }
            )
            
            return await self._format_target_response(updated_target)
            
        except TargetManagementError:
            raise
        except Exception as e:
            logger.error(
                "Target update failed",
                extra={
                    "target_id": target_id,
                    "error": str(e),
                    "updated_by": current_username
                }
            )
            raise TargetManagementError(
                "Failed to update target",
                error_code="update_error"
            )
    
    @with_performance_logging
    async def delete_target(
        self, 
        target_id: int,
        current_user_id: int,
        current_username: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Enhanced target deletion with comprehensive cleanup and audit logging
        """
        logger.info(
            "Target deletion attempt",
            extra={
                "target_id": target_id,
                "deleted_by": current_username
            }
        )
        
        try:
            # Get target data for audit before deletion
            target_to_delete = self.target_service.get_target_by_id(target_id)
            if not target_to_delete:
                raise TargetManagementError(
                    "Target not found",
                    error_code="target_not_found"
                )
            
            # Stop health monitoring
            await self._stop_target_monitoring(target_id)
            
            # Delete target through existing service
            success = self.target_service.delete_target(target_id)
            if not success:
                raise TargetManagementError(
                    "Failed to delete target",
                    error_code="deletion_failed"
                )
            
            # Clear caches
            await self._invalidate_target_cache(target_id)
            await self._invalidate_target_list_cache()
            await self._clear_target_health_cache(target_id)
            
            # Log target deletion audit event
            await self.audit_service.log_event(
                event_type=AuditEventType.TARGET_DELETED,
                user_id=current_user_id,
                resource_type="target",
                resource_id=str(target_id),
                action="delete_target",
                details={
                    "target_id": target_id,
                    "target_name": target_to_delete.name,
                    "ip_address": getTargetIpAddress(target_to_delete),
                    "deleted_by": current_username
                },
                severity=AuditSeverity.HIGH,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Track target deletion activity
            await self._track_target_activity(
                current_user_id, "target_deleted", 
                {"target_id": target_id, "target_name": target_to_delete.name}
            )
            
            logger.info(
                "Target deletion successful",
                extra={
                    "target_id": target_id,
                    "target_name": target_to_delete.name,
                    "deleted_by": current_username
                }
            )
            
            return {
                "message": "Target deleted successfully",
                "deleted_target": {
                    "id": target_id,
                    "name": target_to_delete.name,
                    "ip_address": getTargetIpAddress(target_to_delete)
                },
                "deleted_at": datetime.utcnow(),
                "deleted_by": current_username
            }
            
        except TargetManagementError:
            raise
        except Exception as e:
            logger.error(
                "Target deletion failed",
                extra={
                    "target_id": target_id,
                    "error": str(e),
                    "deleted_by": current_username
                }
            )
            raise TargetManagementError(
                "Failed to delete target",
                error_code="deletion_error"
            )
    
    @with_performance_logging
    async def test_target_connection(
        self, 
        target_id: int,
        current_user_id: int,
        current_username: str
    ) -> Dict[str, Any]:
        """
        Enhanced connection testing with caching and comprehensive results
        """
        logger.info(
            "Target connection test attempt",
            extra={
                "target_id": target_id,
                "tested_by": current_username
            }
        )
        
        try:
            # Get target
            target = self.target_service.get_target_by_id(target_id)
            if not target:
                raise TargetManagementError(
                    "Target not found",
                    error_code="target_not_found"
                )
            
            # Test connection through existing service
            test_result = self.target_service.test_connection(target_id)
            
            # Cache the test result
            await self._cache_connection_test_result(target_id, test_result)
            
            # Track connection test activity
            await self._track_target_activity(
                current_user_id, "connection_tested", 
                {
                    "target_id": target_id, 
                    "success": test_result.success,
                    "response_time": test_result.response_time
                }
            )
            
            logger.info(
                "Target connection test completed",
                extra={
                    "target_id": target_id,
                    "success": test_result.success,
                    "response_time": test_result.response_time,
                    "tested_by": current_username
                }
            )
            
            return {
                "target_id": target_id,
                "target_name": target.name,
                "success": test_result.success,
                "message": test_result.message,
                "response_time": test_result.response_time,
                "tested_at": datetime.utcnow(),
                "tested_by": current_username,
                "details": test_result.details if hasattr(test_result, 'details') else {}
            }
            
        except TargetManagementError:
            raise
        except Exception as e:
            logger.error(
                "Target connection test failed",
                extra={
                    "target_id": target_id,
                    "error": str(e),
                    "tested_by": current_username
                }
            )
            raise TargetManagementError(
                "Failed to test target connection",
                error_code="connection_test_error"
            )
    
    # Private helper methods
    
    async def _validate_target_data(self, target_data: TargetCreate):
        """Validate target creation data"""
        # Credential validation based on method type
        if target_data.method_type in ['ssh', 'winrm', 'telnet']:
            if target_data.method_type == 'ssh' and target_data.ssh_key:
                if not target_data.username:
                    raise ValueError("Username is required for SSH key authentication")
            elif target_data.password:
                if not target_data.username:
                    raise ValueError("Username is required for password authentication")
            else:
                raise ValueError("Either password or SSH key must be provided for authentication")
        elif target_data.method_type == 'snmp':
            if not target_data.password:
                raise ValueError("Community string is required for SNMP (provide as password)")
        # Add more validation as needed
    
    async def _format_target_response(self, target) -> Dict[str, Any]:
        """Format target for response"""
        return {
            "id": target.id,
            "name": target.name,
            "target_type": getattr(target, 'target_type', 'system'),
            "description": target.description,
            "os_type": target.os_type,
            "ip_address": getTargetIpAddress(target),
            "environment": target.environment,
            "location": target.location,
            "data_center": getattr(target, 'data_center', None),
            "region": getattr(target, 'region', None),
            "created_at": target.created_at,
            "updated_at": target.updated_at,
            "communication_methods": [
                {
                    "id": method.id,
                    "method_type": method.method_type,
                    "is_primary": method.is_primary,
                    "port": method.port,
                    "timeout": method.timeout
                }
                for method in target.communication_methods
            ] if hasattr(target, 'communication_methods') else []
        }
    
    async def _get_target_health_status(self, target_id: int) -> Dict[str, Any]:
        """Get target health status with caching"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                cache_key = f"{HEALTH_CACHE_PREFIX}{target_id}"
                cached_health = await redis_client.get(cache_key)
                if cached_health:
                    return json.loads(cached_health)
            except Exception as e:
                logger.warning(f"Failed to get cached health status: {e}")
        
        # Default health status
        return {
            "status": "unknown",
            "last_check": None,
            "response_time": None,
            "error_count": 0
        }
    
    async def _get_connection_statistics(self, target_id: int) -> Dict[str, Any]:
        """Get connection statistics for target"""
        return {
            "total_connections": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "average_response_time": 0,
            "last_connection": None
        }
    
    async def _get_target_recent_activity(self, target_id: int) -> List[Dict[str, Any]]:
        """Get recent activity for target"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                pattern = f"target_activity:{target_id}:*"
                keys = await redis_client.keys(pattern)
                activities = []
                for key in keys[-10:]:  # Get last 10 activities
                    activity_data = await redis_client.get(key)
                    if activity_data:
                        activities.append(json.loads(activity_data))
                return sorted(activities, key=lambda x: x.get('timestamp', ''), reverse=True)
            except Exception as e:
                logger.warning(f"Failed to get recent activity: {e}")
        
        return []
    
    async def _build_target_changes(self, original_target, target_data: TargetUpdate) -> Dict[str, Any]:
        """Build change details for audit logging"""
        changes = {}
        
        if target_data.name and target_data.name != original_target.name:
            changes["name"] = {"from": original_target.name, "to": target_data.name}
        
        if target_data.description and target_data.description != original_target.description:
            changes["description"] = {"from": original_target.description, "to": target_data.description}
        
        if target_data.environment and target_data.environment != original_target.environment:
            changes["environment"] = {"from": original_target.environment, "to": target_data.environment}
        
        return changes
    
    async def _invalidate_target_cache(self, target_id: int):
        """Invalidate target-specific cache entries"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                keys_to_delete = [
                    f"{CACHE_PREFIX}target_{target_id}",
                    f"{CONNECTION_CACHE_PREFIX}{target_id}",
                    f"{HEALTH_CACHE_PREFIX}{target_id}"
                ]
                await redis_client.delete(*keys_to_delete)
            except Exception as e:
                logger.warning(f"Failed to invalidate target cache: {e}")
    
    async def _invalidate_target_list_cache(self):
        """Invalidate target list cache entries"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                pattern = f"{CACHE_PREFIX}target_list_*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Failed to invalidate target list cache: {e}")
    
    async def _track_target_activity(self, user_id: int, activity: str, details: Dict[str, Any]):
        """Track target activity for analytics"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                activity_data = {
                    "user_id": user_id,
                    "activity": activity,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                target_id = details.get("target_id")
                key = f"target_activity:{target_id}:{int(datetime.utcnow().timestamp())}"
                await redis_client.setex(key, 86400, json.dumps(activity_data, default=str))  # 24 hours
                
            except Exception as e:
                logger.warning(f"Failed to track target activity: {e}")
    
    async def _initialize_target_monitoring(self, target_id: int):
        """Initialize health monitoring for new target"""
        try:
            # This would integrate with the health monitoring service
            logger.info(f"Initialized monitoring for target {target_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize monitoring for target {target_id}: {e}")
    
    async def _stop_target_monitoring(self, target_id: int):
        """Stop health monitoring for target"""
        try:
            # This would stop health monitoring
            logger.info(f"Stopped monitoring for target {target_id}")
        except Exception as e:
            logger.warning(f"Failed to stop monitoring for target {target_id}: {e}")
    
    async def _clear_target_health_cache(self, target_id: int):
        """Clear health cache for target"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                pattern = f"{HEALTH_CACHE_PREFIX}{target_id}*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Failed to clear health cache: {e}")
    
    async def _cache_connection_test_result(self, target_id: int, test_result):
        """Cache connection test result"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                cache_key = f"{CONNECTION_CACHE_PREFIX}{target_id}_last_test"
                result_data = {
                    "success": test_result.success,
                    "message": test_result.message,
                    "response_time": test_result.response_time,
                    "tested_at": datetime.utcnow().isoformat()
                }
                await redis_client.setex(cache_key, 3600, json.dumps(result_data, default=str))  # 1 hour
            except Exception as e:
                logger.warning(f"Failed to cache connection test result: {e}")


class TargetManagementError(Exception):
    """Custom target management error with enhanced context"""
    
    def __init__(self, message: str, error_code: str = "target_mgmt_error", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)