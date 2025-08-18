"""
Universal Targets API Router
RESTful API endpoints for target management following the architecture plan.
"""
from typing import List
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.universal_target_service import UniversalTargetService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.user_service import UserService
from app.utils.target_utils import getTargetIpAddress
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.core.security import verify_token
from app.models.user_models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.target_schemas import (
    TargetCreate, 
    TargetUpdate, 
    TargetComprehensiveUpdate,
    TargetResponse, 
    TargetSummary, 
    ConnectionTestResult,
    ErrorResponse,
    CommunicationMethodCreate,
    CommunicationMethodUpdate,
    CommunicationMethodResponse
)
# SerialService removed - using database defaults
from app.models.universal_target_models import UniversalTarget

router = APIRouter(
    prefix="/api/targets",
    tags=["Universal Targets"],
    responses={
        404: {"model": ErrorResponse, "description": "Target not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)

logger = logging.getLogger(__name__)
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


def get_target_service(db: Session = Depends(get_db)) -> UniversalTargetService:
    """Dependency to get target service instance."""
    return UniversalTargetService(db)


@router.get("/", response_model=List[TargetSummary])
async def list_targets(
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Get all targets with summary information.
    
    Returns:
        List[TargetSummary]: List of target summaries
    """
    try:
        summaries = target_service.get_targets_summary()
        return summaries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve targets: {str(e)}"
        )


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Get a specific target by ID with full details.
    
    Args:
        target_id: Target ID
        
    Returns:
        TargetResponse: Complete target information
    """
    target = target_service.get_target_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID {target_id} not found"
        )
    return target


@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new target with communication method and credentials.
    This is an atomic operation that creates the target, communication method, and credentials together.
    
    Supported communication methods:
    - ssh: SSH connection (Linux/Windows)
    - winrm: Windows Remote Management (Windows)
    - snmp: SNMP protocol (Network devices)
    - telnet: Telnet connection (Legacy systems)
    - rest_api: REST API communication (Applications)
    - smtp: SMTP email server (Email systems)
    - mysql: MySQL/MariaDB database
    - postgresql: PostgreSQL database
    - mssql: Microsoft SQL Server database
    - oracle: Oracle database
    - sqlite: SQLite database
    - mongodb: MongoDB database
    - redis: Redis database
    - elasticsearch: Elasticsearch cluster
    
    Args:
        target_data: Target creation data including IP address and credentials
        
    Returns:
        TargetResponse: Created target with full details
    """
    try:
        # Validate credential requirements based on method type
        if target_data.method_type in ['ssh', 'winrm', 'telnet']:
            # Traditional authentication methods
            if target_data.method_type == 'ssh' and target_data.ssh_key:
                if not target_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is required for SSH key authentication"
                    )
            elif target_data.password:
                if not target_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is required for password authentication"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either password or SSH key must be provided for authentication"
                )
        elif target_data.method_type == 'snmp':
            # SNMP requires community string
            if not target_data.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Community string is required for SNMP (provide as password)"
                )
            if not target_data.username:
                target_data.username = 'snmp'  # Default username for SNMP
        elif target_data.method_type == 'rest_api':
            # REST API requires some form of authentication
            if not target_data.password and not target_data.ssh_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API key (as password) or token (as ssh_key) is required for REST API"
                )
            if not target_data.username:
                target_data.username = 'api'  # Default username for API
        elif target_data.method_type == 'smtp':
            # SMTP requires username and password
            if not target_data.username or not target_data.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username and password are required for SMTP authentication"
                )
        elif target_data.method_type in ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 'mongodb', 'redis', 'elasticsearch']:
            # Database methods require username and password (except SQLite)
            if target_data.method_type != 'sqlite':
                if not target_data.username or not target_data.password:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username and password are required for database authentication"
                    )
        
        target = target_service.create_target(
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
            # SMTP-specific fields
            encryption=target_data.encryption,
            server_type=target_data.server_type,
            domain=target_data.domain,
            test_recipient=target_data.test_recipient,
            connection_security=target_data.connection_security,
            # REST API-specific fields
            protocol=getattr(target_data, 'protocol', None),
            base_path=getattr(target_data, 'base_path', None),
            verify_ssl=getattr(target_data, 'verify_ssl', None),
            # SNMP-specific fields
            snmp_version=getattr(target_data, 'snmp_version', None),
            snmp_community=getattr(target_data, 'snmp_community', None),
            snmp_retries=getattr(target_data, 'snmp_retries', None),
            # SNMPv3-specific fields
            snmp_security_level=getattr(target_data, 'snmp_security_level', None),
            snmp_auth_protocol=getattr(target_data, 'snmp_auth_protocol', None),
            snmp_privacy_protocol=getattr(target_data, 'snmp_privacy_protocol', None),
            # Database-specific fields
            database=getattr(target_data, 'database', None),
            charset=getattr(target_data, 'charset', None),
            ssl_mode=getattr(target_data, 'ssl_mode', None),
            driver=getattr(target_data, 'driver', None),
            encrypt=getattr(target_data, 'encrypt', None),
            service_name=getattr(target_data, 'service_name', None),
            sid=getattr(target_data, 'sid', None),
            database_path=getattr(target_data, 'database_path', None),
            auth_source=getattr(target_data, 'auth_source', None),
            ssl=getattr(target_data, 'ssl', None),
            verify_certs=getattr(target_data, 'verify_certs', None)
        )
        
        # Log target creation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_CREATED,
            user_id=current_user.id,
            resource_type="target",
            resource_id=str(target.id),
            action="create_target",
            details={
                "target_name": target.name,
                "ip_address": getTargetIpAddress(target),
                "method_type": target_data.method_type,
                "created_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return target
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create target: {str(e)}"
        )


@router.post("/comprehensive", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target_comprehensive(
    target_data: TargetComprehensiveUpdate,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new target with comprehensive support for multiple communication methods.
    
    This endpoint supports:
    - Multiple communication methods per target
    - Primary method designation
    - Complex method configurations
    - Multiple credentials per method
    
    Args:
        target_data: Comprehensive target creation data
        
    Returns:
        TargetResponse: Created target with full details
    """
    try:
        # Validate required fields
        if not target_data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target name is required"
            )
        
        if not target_data.os_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OS type is required"
            )
        
        if not target_data.communication_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one communication method is required"
            )
        
        # Create the target directly without using the basic create_target method
        # Create the target (target_serial will be auto-generated by database)
        target = UniversalTarget(
            name=target_data.name,
            target_type="system",  # Simplified version only supports system targets
            description=target_data.description,
            os_type=target_data.os_type,
            environment=target_data.environment or "development",
            location=target_data.location,
            data_center=target_data.data_center,
            region=target_data.region,
            status="active",
            health_status="unknown"
        )
        
        db.add(target)
        db.flush()  # Get the target ID
        
        # Now add the communication methods
        updated_target = target_service.update_target_comprehensive(
            target_id=target.id,
            communication_methods=[method.dict() for method in target_data.communication_methods]
        )
        
        if not updated_target:
            # Clean up the target if comprehensive update fails
            db.delete(target)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add communication methods to target"
            )
        
        # Log comprehensive target creation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_CREATED,
            user_id=current_user.id,
            resource_type="target",
            resource_id=str(updated_target.id),
            action="create_target_comprehensive",
            details={
                "target_name": updated_target.name,
                "ip_address": getTargetIpAddress(updated_target),
                "communication_methods_count": len(updated_target.communication_methods),
                "created_by": current_user.username,
                "endpoint": "comprehensive"
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return updated_target
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating target comprehensively: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create target comprehensively: {str(e)}"
        )


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update target basic information.
    Note: Communication methods and credentials are managed separately.
    
    Args:
        target_id: Target ID to update
        target_data: Updated target data
        
    Returns:
        TargetResponse: Updated target information
    """
    try:
        target = target_service.update_target(
            target_id=target_id,
            name=target_data.name,
            description=target_data.description,
            os_type=target_data.os_type,
            environment=target_data.environment,
            location=target_data.location,
            data_center=target_data.data_center,
            region=target_data.region,
            status=target_data.status
        )
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        # Log target update audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_UPDATED,
            user_id=current_user.id,
            resource_type="target",
            resource_id=str(target_id),
            action="update_target",
            details={
                "target_name": target.name,
                "ip_address": getTargetIpAddress(target),
                "updated_fields": {
                    "name": target_data.name,
                    "description": target_data.description,
                    "os_type": target_data.os_type,
                    "environment": target_data.environment,
                    "location": target_data.location,
                    "status": target_data.status
                },
                "updated_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return target
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update target: {str(e)}"
        )


@router.put("/{target_id}/comprehensive", response_model=TargetResponse)
async def update_target_comprehensive(
    target_id: int,
    target_data: TargetComprehensiveUpdate,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Comprehensive update of target including basic info, communication methods, and credentials.
    
    Args:
        target_id: Target ID to update
        target_data: Comprehensive target update data
        
    Returns:
        TargetResponse: Updated target information with all relationships
    """
    try:
        target = target_service.update_target_comprehensive(
            target_id=target_id,
            name=target_data.name,
            description=target_data.description,
            os_type=target_data.os_type,
            environment=target_data.environment,
            location=target_data.location,
            data_center=target_data.data_center,
            region=target_data.region,
            status=target_data.status,
            ip_address=target_data.ip_address,
            communication_methods=[method.dict() for method in target_data.communication_methods] if target_data.communication_methods else None,
            # Legacy single method support
            method_type=target_data.method_type,
            port=target_data.port,
            username=target_data.username,
            password=target_data.password,
            ssh_key=target_data.ssh_key,
            ssh_passphrase=target_data.ssh_passphrase
        )
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        return target
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update target comprehensively: {str(e)}"
        )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a target (soft delete - sets is_active = False).
    
    Args:
        target_id: Target ID to delete
    """
    # Get target data for audit before deletion
    target = target_service.get_target_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID {target_id} not found"
        )
    
    success = target_service.delete_target(target_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID {target_id} not found"
        )
    
    # Log target deletion audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.TARGET_DELETED,
        user_id=current_user.id,
        resource_type="target",
        resource_id=str(target_id),
        action="delete_target",
        details={
            "target_name": target.name,
            "ip_address": getTargetIpAddress(target),
            "os_type": target.os_type,
            "environment": target.environment,
            "deleted_by": current_user.username
        },
        severity=AuditSeverity.HIGH,  # Target deletion is high severity
        ip_address=client_ip,
        user_agent=user_agent
    )


@router.post("/{target_id}/test-connection", response_model=ConnectionTestResult)
async def test_target_connection(
    target_id: int,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test connection to a target.
    Note: This is a placeholder for future implementation.
    
    Args:
        target_id: Target ID to test
        
    Returns:
        ConnectionTestResult: Test results
    """
    try:
        result = target_service.test_target_connection(target_id)
        
        # Log connection test audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get target info for audit
        target = target_service.get_target_by_id(target_id)
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_CONNECTION_TEST,
            user_id=current_user.id,
            resource_type="target",
            resource_id=str(target_id),
            action="test_connection",
            details={
                "target_name": target.name if target else f"target_{target_id}",
                "ip_address": getTargetIpAddress(target) if target else "unknown",
                "test_result": result.success if hasattr(result, 'success') else "unknown",
                "tested_by": current_user.username
            },
            severity=AuditSeverity.LOW,  # Connection tests are low severity
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )


# UUID-based endpoints for permanent references
@router.get("/uuid/{target_uuid}", response_model=TargetResponse)
async def get_target_by_uuid(
    target_uuid: str,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Get target by UUID (permanent identifier)"""
    try:
        target = target_service.get_target_by_uuid(target_uuid)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with UUID {target_uuid} not found"
            )
        return TargetResponse.from_orm(target)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target by UUID: {str(e)}"
        )


@router.get("/serial/{target_serial}", response_model=TargetResponse)
async def get_target_by_serial(
    target_serial: str,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Get target by serial number (human-readable permanent identifier)"""
    try:
        target = target_service.get_target_by_serial(target_serial)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with serial {target_serial} not found"
            )
        return TargetResponse.from_orm(target)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target by serial: {str(e)}"
        )


# Communication Methods Management Endpoints
@router.post("/{target_id}/communication-methods", response_model=CommunicationMethodResponse)
async def add_communication_method(
    target_id: int,
    method_data: CommunicationMethodCreate,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Add a new communication method to a target.
    
    Args:
        target_id: Target ID to add method to
        method_data: Communication method and credential data
        
    Returns:
        CommunicationMethodResponse: Created communication method
    """
    try:
        method = target_service.add_communication_method(
            target_id=target_id,
            method_type=method_data.method_type,
            config=method_data.config,
            is_primary=method_data.is_primary,
            is_active=method_data.is_active,
            priority=method_data.priority,
            credential_type=method_data.credential_type,
            username=method_data.username,
            password=method_data.password,
            ssh_key=method_data.ssh_key,
            ssh_passphrase=method_data.ssh_passphrase
        )
        
        if not method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        return method
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add communication method: {str(e)}"
        )


@router.put("/{target_id}/communication-methods/{method_id}", response_model=CommunicationMethodResponse)
async def update_communication_method(
    target_id: int,
    method_id: int,
    method_data: CommunicationMethodUpdate,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Update a communication method.
    
    Args:
        target_id: Target ID
        method_id: Communication method ID to update
        method_data: Updated method data
        
    Returns:
        CommunicationMethodResponse: Updated communication method
    """
    try:
        method = target_service.update_communication_method(
            target_id=target_id,
            method_id=method_id,
            method_type=method_data.method_type,
            config=method_data.config,
            is_primary=method_data.is_primary,
            is_active=method_data.is_active,
            priority=method_data.priority
        )
        
        if not method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication method with ID {method_id} not found"
            )
        
        return method
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update communication method: {str(e)}"
        )


@router.delete("/{target_id}/communication-methods/{method_id}")
async def delete_communication_method(
    target_id: int,
    method_id: int,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Delete a communication method.
    
    Args:
        target_id: Target ID
        method_id: Communication method ID to delete
        
    Returns:
        dict: Success message
    """
    try:
        success = target_service.delete_communication_method(target_id, method_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication method with ID {method_id} not found"
            )
        
        return {"message": "Communication method deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete communication method: {str(e)}"
        )


@router.post("/{target_id}/communication-methods/{method_id}/test", response_model=ConnectionTestResult)
async def test_communication_method(
    target_id: int,
    method_id: int,
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """
    Test connection using a specific communication method.
    
    Args:
        target_id: Target ID
        method_id: Communication method ID to test
        
    Returns:
        ConnectionTestResult: Test results for this specific method
    """
    try:
        result = target_service.test_communication_method(target_id, method_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test communication method: {str(e)}"
        )


# Health Monitoring Endpoints

@router.post("/{target_id}/health-check")
async def check_target_health(
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger a health check for a specific target.
    
    Args:
        target_id: Target ID to check
        
    Returns:
        dict: Health check result
    """
    try:
        # Get target
        target_service = UniversalTargetService(db)
        target = target_service.get_target_by_id(target_id)
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        # Perform health check
        health_service = HealthMonitoringService(db)
        health_result = health_service.check_target_health(target)
        
        # Update health status
        status_updated = health_service.update_target_health_status(target_id, health_result)
        
        return {
            "target_id": target_id,
            "target_name": target.name,
            "health_check_result": health_result,
            "status_updated": status_updated,
            "timestamp": target.updated_at.isoformat() if target.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check target health: {str(e)}"
        )


@router.post("/health-check-batch")
async def run_health_check_batch(
    batch_size: int = 10,
    db: Session = Depends(get_db)
):
    """
    Manually trigger a health check batch for multiple targets.
    
    Args:
        batch_size: Number of targets to check in this batch
        
    Returns:
        dict: Batch health check results
    """
    try:
        health_service = HealthMonitoringService(db)
        results = health_service.run_health_check_batch(batch_size)
        
        return {
            "batch_size": batch_size,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run health check batch: {str(e)}"
        )


@router.get("/health-monitoring/settings")
async def get_health_monitoring_settings():
    """
    Get current health monitoring configuration settings.
    
    Returns:
        dict: Health monitoring settings
    """
    from app.config.health_monitoring import (
        DEFAULT_HEALTH_CHECK_INTERVALS,
        HEALTH_CHECK_TIMEOUTS,
        HEALTH_THRESHOLDS,
        HEALTH_MONITORING_SETTINGS
    )
    
    return {
        "enabled": HEALTH_MONITORING_SETTINGS['enabled'],
        "intervals": DEFAULT_HEALTH_CHECK_INTERVALS,
        "timeouts": HEALTH_CHECK_TIMEOUTS,
        "thresholds": HEALTH_THRESHOLDS,
        "settings": HEALTH_MONITORING_SETTINGS
    }


@router.post("/test-method-config", response_model=ConnectionTestResult)
async def test_method_configuration(
    method_config: dict,
    db: Session = Depends(get_db)
):
    """
    Test a communication method configuration before saving.
    This allows testing method configs during create/edit without saving first.
    
    Args:
        method_config: Method configuration to test
        
    Returns:
        ConnectionTestResult: Test results
    """
    try:
        from app.utils.connection_test_utils import (
            test_ssh_connection, test_winrm_connection, test_smtp_connection,
            test_snmp_connection, test_telnet_connection, test_rest_api_connection
        )
        
        method_type = method_config.get('method_type')
        config = method_config.get('config', {})
        credentials = method_config.get('credentials', {})
        
        if not method_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="method_type is required"
            )
        
        host = config.get('host')
        port = config.get('port')
        
        if not host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="host is required in config"
            )
        
        # Extract credentials
        encrypted_creds = credentials.get('encrypted_credentials', {})
        cred_type = credentials.get('credential_type', 'password')
        
        # Format credentials for testing
        test_creds = {
            'type': 'ssh_key' if cred_type == 'ssh_key' else 'password',
            'username': encrypted_creds.get('username')
        }
        
        if cred_type == 'password':
            test_creds['password'] = encrypted_creds.get('password')
        else:
            test_creds['private_key'] = encrypted_creds.get('ssh_key')
        
        # Test connection based on method type
        if method_type == 'ssh':
            if not port:
                port = 22
            result = test_ssh_connection(host, port, test_creds, timeout=15)
        elif method_type == 'winrm':
            if not port:
                port = 5985
            result = test_winrm_connection(host, port, test_creds, timeout=20)
        elif method_type == 'smtp':
            if not port:
                port = 587
            result = test_smtp_connection(host, port, test_creds, config, timeout=20)
        elif method_type == 'snmp':
            if not port:
                port = 161
            result = test_snmp_connection(host, port, test_creds, timeout=10)
        elif method_type == 'telnet':
            if not port:
                port = 23
            result = test_telnet_connection(host, port, test_creds, timeout=15)
        elif method_type == 'rest_api':
            if not port:
                port = 80
            result = test_rest_api_connection(host, port, test_creds, config, timeout=30)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported method type: {method_type}"
            )
        
        return ConnectionTestResult(
            success=result['success'],
            message=result['message'],
            details=result.get('details', {}),
            response_time=result.get('response_time'),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test method configuration: {str(e)}"
        )

