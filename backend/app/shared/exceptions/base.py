"""
Base exception classes for the ENABLEDRM platform.
"""
from typing import Optional, Dict, Any


class ENABLEDRMException(Exception):
    """Base exception for all ENABLEDRM-specific errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DomainException(ENABLEDRMException):
    """Base exception for domain-specific business logic errors."""
    pass


class InfrastructureException(ENABLEDRMException):
    """Base exception for infrastructure-related errors."""
    pass


class ValidationException(DomainException):
    """Exception raised when domain validation fails."""
    pass


class NotFoundError(DomainException):
    """Exception raised when a requested resource is not found."""
    pass


class ConflictError(DomainException):
    """Exception raised when a resource conflict occurs."""
    pass


class UnauthorizedError(DomainException):
    """Exception raised when user is not authorized to perform an action."""
    pass


class DatabaseError(InfrastructureException):
    """Exception raised when database operations fail."""
    pass


class ExternalServiceError(InfrastructureException):
    """Exception raised when external service calls fail."""
    pass