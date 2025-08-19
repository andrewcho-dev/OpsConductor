"""
Audit logging utilities for consistent audit event logging across the application.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Union
from fastapi import Request
from sqlalchemy.orm import Session

from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

async def log_audit_event(
    db: Session,
    event_type: Union[AuditEventType, str],
    user_id: Optional[int],
    resource_type: str,
    resource_id: Optional[str],
    action: str,
    details: Dict[str, Any],
    severity: Union[AuditSeverity, str] = AuditSeverity.MEDIUM,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request: Optional[Request] = None
) -> None:
    """
    Log an audit event asynchronously.
    
    Args:
        db: Database session
        event_type: Type of audit event (can be string or enum)
        user_id: ID of the user who performed the action
        resource_type: Type of resource affected
        resource_id: ID of the resource affected
        action: Action performed
        details: Additional details about the event
        severity: Severity level of the event
        ip_address: IP address of the client
        user_agent: User agent of the client
        request: FastAPI request object (if available, will extract IP and user agent)
    """
    try:
        # Convert string event_type to enum if needed
        if isinstance(event_type, str):
            try:
                event_type = AuditEventType(event_type)
            except ValueError:
                logger.warning(f"Unknown audit event type: {event_type}, using as-is")
        
        # Convert string severity to enum if needed
        if isinstance(severity, str):
            try:
                severity = AuditSeverity(severity)
            except ValueError:
                severity = AuditSeverity.MEDIUM
                logger.warning(f"Unknown audit severity: {severity}, using MEDIUM")
        
        # Extract IP and user agent from request if available
        if request and not ip_address:
            ip_address = request.client.host if request.client else "unknown"
        
        if request and not user_agent:
            user_agent = request.headers.get("user-agent", "unknown")
        
        # Create audit service and log event
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")


def log_audit_event_sync(
    db: Session,
    event_type: Union[AuditEventType, str],
    user_id: Optional[int],
    resource_type: str,
    resource_id: Optional[str],
    action: str,
    details: Dict[str, Any],
    severity: Union[AuditSeverity, str] = AuditSeverity.MEDIUM,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request: Optional[Request] = None
) -> None:
    """
    Synchronous wrapper for log_audit_event.
    Creates a background task to log the audit event.
    
    This function can be called from synchronous code.
    """
    try:
        # Create a background task for async logging
        asyncio.create_task(log_audit_event(
            db=db,
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            request=request
        ))
    except RuntimeError:
        # If not in an async context, log a warning
        logger.warning("Cannot create async task for audit logging outside of async context")
        # Fallback to direct logging in a separate thread
        import threading
        threading.Thread(
            target=lambda: asyncio.run(log_audit_event(
                db=db,
                event_type=event_type,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                request=request
            ))
        ).start()