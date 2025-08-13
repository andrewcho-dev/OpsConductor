"""
Global error handling middleware for ENABLEDRM platform.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
import uuid
from datetime import datetime

from app.shared.exceptions.base import (
    ENABLEDRMException, DomainException, InfrastructureException,
    ValidationException, NotFoundError, ConflictError, UnauthorizedError
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all exceptions globally."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any exceptions."""
        error_id = str(uuid.uuid4())
        
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # FastAPI HTTPExceptions should pass through
            raise e
        except ENABLEDRMException as e:
            # Handle our custom domain exceptions
            return await self._handle_domain_exception(e, error_id, request)
        except Exception as e:
            # Handle unexpected exceptions
            return await self._handle_unexpected_exception(e, error_id, request)
    
    async def _handle_domain_exception(
        self, 
        exception: ENABLEDRMException, 
        error_id: str, 
        request: Request
    ) -> JSONResponse:
        """Handle domain-specific exceptions."""
        
        # Log the error
        logger.warning(
            f"Domain exception [{error_id}]: {exception.message}",
            extra={
                "error_id": error_id,
                "error_code": exception.error_code,
                "details": exception.details,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        # Map exception types to HTTP status codes
        status_code_map = {
            ValidationException: 400,
            ConflictError: 409,
            NotFoundError: 404,
            UnauthorizedError: 401,
            DomainException: 400,
            InfrastructureException: 500
        }
        
        status_code = status_code_map.get(type(exception), 500)
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": {
                    "message": exception.message,
                    "error_code": exception.error_code,
                    "error_id": error_id,
                    "details": exception.details
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _handle_unexpected_exception(
        self, 
        exception: Exception, 
        error_id: str, 
        request: Request
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        
        # Log the full traceback for debugging
        logger.error(
            f"Unexpected exception [{error_id}]: {str(exception)}",
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "message": "An unexpected error occurred",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "error_id": error_id,
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Log request details."""
        start_time = datetime.utcnow()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - {duration:.3f}s",
            extra={
                "status_code": response.status_code,
                "duration_seconds": duration,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return response