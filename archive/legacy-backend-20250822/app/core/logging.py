"""
Structured Logging Utility
Provides structured logging with JSON formatting and contextual information

PHASE 2 IMPROVEMENTS:
- ✅ Structured JSON logging
- ✅ Contextual information
- ✅ Performance metrics
- ✅ Request tracing
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import os
import sys
from functools import wraps


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add process/thread info
        log_entry["process_id"] = os.getpid()
        log_entry["thread_id"] = record.thread
        
        return json.dumps(log_entry, default=str)


def get_structured_logger(name: str) -> logging.Logger:
    """Get a structured logger instance"""
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


class PerformanceLogger:
    """Performance logging utility"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_operation(self, operation: str, duration: float, success: bool = True, **kwargs):
        """Log operation performance"""
        self.logger.info(
            f"Operation {operation} completed",
            extra={
                "operation": operation,
                "duration_seconds": round(duration, 4),
                "success": success,
                **kwargs
            }
        )
    
    def log_query(self, query_type: str, duration: float, result_count: int = None, **kwargs):
        """Log database query performance"""
        extra_data = {
            "query_type": query_type,
            "duration_seconds": round(duration, 4),
            **kwargs
        }
        
        if result_count is not None:
            extra_data["result_count"] = result_count
        
        self.logger.info(
            f"Database query {query_type} executed",
            extra=extra_data
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, duration: float = None):
        """Log cache operation"""
        extra_data = {
            "cache_operation": operation,
            "cache_key": key
        }
        
        if hit is not None:
            extra_data["cache_hit"] = hit
        
        if duration is not None:
            extra_data["duration_seconds"] = round(duration, 4)
        
        self.logger.info(
            f"Cache {operation} operation",
            extra=extra_data
        )


def performance_monitor(operation_name: str = None):
    """Decorator for monitoring function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            perf_logger = PerformanceLogger(logger)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                perf_logger.log_operation(
                    operation=op_name,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                perf_logger.log_operation(
                    operation=op_name,
                    duration=duration,
                    success=False,
                    error=str(e)
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            perf_logger = PerformanceLogger(logger)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                perf_logger.log_operation(
                    operation=op_name,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                perf_logger.log_operation(
                    operation=op_name,
                    duration=duration,
                    success=False,
                    error=str(e)
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RequestLogger:
    """Request-specific logging utility"""
    
    def __init__(self, logger: logging.Logger, request_id: str = None):
        self.logger = logger
        self.request_id = request_id or f"req_{int(time.time() * 1000)}"
    
    def log_request_start(self, method: str, path: str, user_id: str = None):
        """Log request start"""
        self.logger.info(
            "Request started",
            extra={
                "request_id": self.request_id,
                "method": method,
                "path": path,
                "user_id": user_id,
                "event": "request_start"
            }
        )
    
    def log_request_end(self, status_code: int, duration: float):
        """Log request completion"""
        self.logger.info(
            "Request completed",
            extra={
                "request_id": self.request_id,
                "status_code": status_code,
                "duration_seconds": round(duration, 4),
                "event": "request_end"
            }
        )
    
    def log_validation_error(self, field: str, error: str):
        """Log validation error"""
        self.logger.warning(
            "Request validation failed",
            extra={
                "request_id": self.request_id,
                "validation_field": field,
                "validation_error": error,
                "event": "validation_error"
            }
        )
    
    def log_business_logic_error(self, operation: str, error: str):
        """Log business logic error"""
        self.logger.error(
            "Business logic error",
            extra={
                "request_id": self.request_id,
                "operation": operation,
                "error": error,
                "event": "business_error"
            }
        )


def get_request_logger(request_id: str = None) -> RequestLogger:
    """Get a request-specific logger"""
    logger = get_structured_logger("request")
    return RequestLogger(logger, request_id)


# Application-wide loggers
app_logger = get_structured_logger("app")
security_logger = get_structured_logger("security")
performance_logger = PerformanceLogger(get_structured_logger("performance"))