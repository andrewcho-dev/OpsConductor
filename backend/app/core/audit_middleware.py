"""
Middleware for logging API access events.
"""
import time
import logging
import asyncio
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.audit_utils import log_audit_event
from app.domains.audit.services.audit_service import AuditEventType, AuditSeverity
from app.database.database import get_db

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API access events."""
    
    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            exclude_paths: List of paths to exclude from audit logging
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/metrics",
            "/health",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log API access.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next middleware or route handler
        """
        # Skip logging for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request details
        method = request.method
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract user ID from request state if available
        user_id = None
        try:
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.get("id")
        except Exception:
            pass
        
        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log successful API access
            await self._log_api_access(
                request=request,
                path=path,
                method=method,
                status_code=status_code,
                user_id=user_id,
                client_host=client_host,
                user_agent=user_agent,
                execution_time=execution_time
            )
            
            return response
            
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log failed API access
            await self._log_api_access(
                request=request,
                path=path,
                method=method,
                status_code=500,
                user_id=user_id,
                client_host=client_host,
                user_agent=user_agent,
                execution_time=execution_time,
                error=str(e)
            )
            
            # Re-raise the exception
            raise
    
    async def _log_api_access(
        self,
        request: Request,
        path: str,
        method: str,
        status_code: int,
        user_id: Optional[int],
        client_host: str,
        user_agent: str,
        execution_time: float,
        error: Optional[str] = None
    ) -> None:
        """
        Log API access event.
        
        Args:
            request: The request object
            path: The request path
            method: The HTTP method
            status_code: The response status code
            user_id: The ID of the authenticated user
            client_host: The client host
            user_agent: The user agent
            execution_time: The execution time in seconds
            error: The error message if any
        """
        try:
            # Determine event type and severity based on status code
            event_type = AuditEventType.API_ACCESS
            
            if status_code >= 400:
                severity = AuditSeverity.MEDIUM
                if status_code >= 500:
                    severity = AuditSeverity.HIGH
                    event_type = AuditEventType.API_ERROR
            else:
                severity = AuditSeverity.INFO
            
            # Get query parameters (excluding sensitive data)
            query_params = dict(request.query_params)
            for sensitive_param in ["password", "token", "key", "secret", "auth"]:
                if sensitive_param in query_params:
                    query_params[sensitive_param] = "***REDACTED***"
            
            # Create details
            details = {
                "path": path,
                "method": method,
                "status_code": status_code,
                "execution_time_ms": int(execution_time * 1000),
                "query_params": query_params,
                "headers": {
                    k: v for k, v in request.headers.items() 
                    if k.lower() not in ["authorization", "cookie"]
                }
            }
            
            # Add error details if available
            if error:
                details["error"] = error
            
            # Get database session
            try:
                db = next(get_db())
                
                # Log the event
                await log_audit_event(
                    db=db,
                    event_type=event_type,
                    user_id=user_id,
                    resource_type="api",
                    resource_id=path,
                    action=method,
                    details=details,
                    severity=severity,
                    ip_address=client_host,
                    user_agent=user_agent
                )
            except Exception as db_error:
                logger.error(f"Failed to log API access event: {str(db_error)}")
                
        except Exception as e:
            logger.error(f"Error in API audit logging: {str(e)}")


# Add new event types to AuditEventType enum
if not hasattr(AuditEventType, 'API_ACCESS'):
    AuditEventType.API_ACCESS = "api_access"

if not hasattr(AuditEventType, 'API_ERROR'):
    AuditEventType.API_ERROR = "api_error"