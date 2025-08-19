"""
Authentication Service Layer - Phase 2
Business logic separation with caching and comprehensive logging

PHASE 2 IMPROVEMENTS:
- ✅ Service layer architecture with business logic separation
- ✅ Redis caching for sessions and rate limiting
- ✅ Structured JSON logging with contextual information
- ✅ Performance monitoring and metrics collection
- ✅ Enhanced security with advanced rate limiting
- ✅ Session management and token blacklisting
"""

import logging
import time
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.logging import get_structured_logger
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

# Configure structured logger
logger = get_structured_logger(__name__)

# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "auth:"
SESSION_CACHE_PREFIX = "session:"
RATE_LIMIT_PREFIX = "rate_limit:"
TOKEN_BLACKLIST_PREFIX = "blacklist:"


def with_performance_logging(func):
    """Performance logging decorator for auth operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "Auth service operation successful",
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
                "Auth service operation failed",
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
    """Caching decorator for auth operations"""
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
                            "Cache hit for auth operation",
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
                        "Cached auth operation result",
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


class AuthService:
    """Enhanced authentication service with caching and comprehensive logging"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.user_service = UserService()
        logger.info("Auth Service initialized with enhanced features")
    
    @with_performance_logging
    async def authenticate_user(
        self, 
        username: str, 
        password: str, 
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """
        Enhanced user authentication with comprehensive security features
        """
        logger.info(
            "User authentication attempt",
            extra={
                "username": username,
                "ip_address": ip_address,
                "remember_me": remember_me
            }
        )
        
        # Check rate limiting
        if await self._is_rate_limited(ip_address):
            logger.warning(
                "Authentication blocked due to rate limiting",
                extra={
                    "username": username,
                    "ip_address": ip_address,
                    "reason": "rate_limited"
                }
            )
            raise AuthenticationError(
                "Too many failed attempts. Please try again later.",
                error_code="rate_limited",
                details={"retry_after": 3600}
            )
        
        # Authenticate user
        user = self.user_service.authenticate_user(self.db, username, password)
        
        if not user:
            # Track failed attempt
            await self._track_failed_attempt(username, ip_address, user_agent)
            
            logger.warning(
                "Authentication failed - invalid credentials",
                extra={
                    "username": username,
                    "ip_address": ip_address,
                    "reason": "invalid_credentials"
                }
            )
            
            raise AuthenticationError(
                "Invalid username or password",
                error_code="invalid_credentials"
            )
        
        # Clear failed attempts on successful login
        await self._clear_failed_attempts(ip_address)
        
        # Update last login
        self.user_service.update_last_login(self.db, user.id)
        
        # Create session
        session_id = await self._create_user_session(
            user.id, ip_address, user_agent, remember_me
        )
        
        # Generate tokens
        tokens = await self._generate_tokens(user, remember_me)
        
        # Log successful authentication
        await self.audit_service.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            action="login",
            details={
                "username": user.username,
                "login_method": "password",
                "ip_address": ip_address,
                "user_agent": user_agent,
                "remember_me": remember_me,
                "session_id": session_id
            },
            severity=AuditSeverity.LOW,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            "User authentication successful",
            extra={
                "user_id": user.id,
                "username": user.username,
                "ip_address": ip_address,
                "session_id": session_id
            }
        )
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            },
            "tokens": tokens,
            "session_id": session_id
        }
    
    @with_performance_logging
    async def logout_user(
        self, 
        token: str, 
        ip_address: str, 
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Enhanced user logout with token blacklisting and session cleanup
        """
        logger.info(
            "User logout attempt",
            extra={
                "ip_address": ip_address
            }
        )
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            logger.warning(
                "Logout attempt with invalid token",
                extra={
                    "ip_address": ip_address
                }
            )
            raise AuthenticationError(
                "Invalid or expired token",
                error_code="invalid_token"
            )
        
        user_id = payload.get("user_id")
        username = payload.get("sub")
        
        # Calculate session duration
        login_time = payload.get("iat", int(datetime.utcnow().timestamp()))
        logout_time = datetime.utcnow()
        session_duration = int(logout_time.timestamp() - login_time)
        
        # Blacklist token
        await self._blacklist_token(token, payload.get("exp", 0))
        
        # Clear session cache
        await self._clear_user_session(user_id)
        
        # Log logout event
        await self.audit_service.log_event(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id) if user_id else "unknown",
            action="logout",
            details={
                "username": username,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_duration_seconds": session_duration,
                "logout_method": "explicit"
            },
            severity=AuditSeverity.LOW,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            "User logout successful",
            extra={
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "session_duration": session_duration
            }
        )
        
        return {
            "message": "Successfully logged out",
            "logged_out_at": logout_time,
            "session_duration": session_duration
        }
    
    @with_performance_logging
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Enhanced token refresh with validation and caching
        """
        logger.info("Token refresh attempt")
        
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload:
            logger.warning("Token refresh with invalid token")
            raise AuthenticationError(
                "Invalid or expired refresh token",
                error_code="invalid_refresh_token"
            )
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if not username or not user_id:
            raise AuthenticationError(
                "Invalid token payload",
                error_code="invalid_token_payload"
            )
        
        # Check if token is blacklisted
        if await self._is_token_blacklisted(refresh_token):
            logger.warning(
                "Token refresh with blacklisted token",
                extra={
                    "user_id": user_id,
                    "username": username
                }
            )
            raise AuthenticationError(
                "Token has been revoked",
                error_code="token_revoked"
            )
        
        # Verify user still exists and is active
        user = self.user_service.get_user_by_id(self.db, user_id)
        if not user or not user.is_active:
            logger.warning(
                "Token refresh for inactive/missing user",
                extra={
                    "user_id": user_id,
                    "username": username
                }
            )
            raise AuthenticationError(
                "User not found or account is inactive",
                error_code="user_not_found_or_inactive"
            )
        
        # Generate new tokens
        tokens = await self._generate_tokens(user)
        
        logger.info(
            "Token refresh successful",
            extra={
                "user_id": user_id,
                "username": username
            }
        )
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            },
            "tokens": tokens
        }
    
    @with_caching(lambda self, user_id: f"user_info_{user_id}", ttl=1800)  # 30 minutes
    @with_performance_logging
    async def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """
        Get user information with caching
        """
        logger.info(
            "Retrieving user information",
            extra={"user_id": user_id}
        )
        
        user = self.user_service.get_user_by_id(self.db, user_id)
        if not user:
            logger.warning(
                "User info request for non-existent user",
                extra={"user_id": user_id}
            )
            raise AuthenticationError(
                "User not found",
                error_code="user_not_found"
            )
        
        # Get user permissions
        permissions = self._get_user_permissions(user.role)
        
        logger.info(
            "User information retrieved",
            extra={
                "user_id": user.id,
                "username": user.username
            }
        )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "permissions": permissions
        }
    
    # Private helper methods
    
    async def _is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP address is rate limited"""
        redis_client = get_redis_client()
        if not redis_client:
            return False
        
        try:
            key = f"{RATE_LIMIT_PREFIX}{ip_address}"
            failed_attempts = await redis_client.get(key)
            return int(failed_attempts or 0) >= 10
        except Exception as e:
            logger.warning(
                "Rate limit check failed",
                extra={
                    "ip_address": ip_address,
                    "error": str(e)
                }
            )
            return False
    
    async def _track_failed_attempt(self, username: str, ip_address: str, user_agent: str):
        """Track failed authentication attempt"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                key = f"{RATE_LIMIT_PREFIX}{ip_address}"
                failed_attempts = await redis_client.get(key) or 0
                failed_attempts = int(failed_attempts) + 1
                await redis_client.setex(key, 3600, failed_attempts)  # 1 hour TTL
                
                # Determine severity
                if failed_attempts >= 10:
                    severity = AuditSeverity.CRITICAL
                    action = "potential_brute_force_attack"
                elif failed_attempts >= 5:
                    severity = AuditSeverity.HIGH
                    action = "multiple_failed_logins"
                else:
                    severity = AuditSeverity.HIGH
                    action = "failed_login"
                
                # Log security event
                await self.audit_service.log_event(
                    event_type=AuditEventType.SECURITY_VIOLATION,
                    user_id=None,
                    resource_type="authentication",
                    resource_id=username,
                    action=action,
                    details={
                        "username": username,
                        "reason": "invalid_credentials",
                        "ip_address": ip_address,
                        "user_agent": user_agent,
                        "failed_attempts_count": failed_attempts,
                        "potential_brute_force": failed_attempts >= 10
                    },
                    severity=severity,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
            except Exception as e:
                logger.error(
                    "Failed to track failed attempt",
                    extra={
                        "ip_address": ip_address,
                        "error": str(e)
                    }
                )
    
    async def _clear_failed_attempts(self, ip_address: str):
        """Clear failed attempts for IP address"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                key = f"{RATE_LIMIT_PREFIX}{ip_address}"
                await redis_client.delete(key)
            except Exception as e:
                logger.warning(
                    "Failed to clear failed attempts",
                    extra={
                        "ip_address": ip_address,
                        "error": str(e)
                    }
                )
    
    async def _create_user_session(
        self, 
        user_id: int, 
        ip_address: str, 
        user_agent: str, 
        remember_me: bool = False
    ) -> str:
        """Create user session with caching"""
        session_id = f"sess_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "login_time": datetime.utcnow().isoformat(),
            "remember_me": remember_me
        }
        
        # Cache session data
        redis_client = get_redis_client()
        if redis_client:
            try:
                ttl = 7 * 24 * 3600 if remember_me else 24 * 3600  # 7 days or 1 day
                await redis_client.setex(
                    f"{SESSION_CACHE_PREFIX}{session_id}",
                    ttl,
                    json.dumps(session_data, default=str)
                )
            except Exception as e:
                logger.warning(
                    "Failed to cache session data",
                    extra={
                        "session_id": session_id,
                        "error": str(e)
                    }
                )
        
        # Also create database session
        self.user_service.create_user_session(
            self.db, user_id, ip_address=ip_address, user_agent=user_agent
        )
        
        return session_id
    
    async def _clear_user_session(self, user_id: int):
        """Clear user session from cache"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                # Find and delete session keys for user
                pattern = f"{SESSION_CACHE_PREFIX}sess_{user_id}_*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.warning(
                    "Failed to clear user session",
                    extra={
                        "user_id": user_id,
                        "error": str(e)
                    }
                )
    
    async def _generate_tokens(self, user, remember_me: bool = False) -> Dict[str, Any]:
        """Generate access and refresh tokens"""
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * (7 if remember_me else 1)
        )
        expires_at = datetime.utcnow() + access_token_expires
        
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "expires_at": expires_at
        }
    
    async def _blacklist_token(self, token: str, exp: int):
        """Add token to blacklist"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                # Calculate TTL based on token expiration
                current_time = int(datetime.utcnow().timestamp())
                ttl = max(exp - current_time, 0)
                
                if ttl > 0:
                    await redis_client.setex(
                        f"{TOKEN_BLACKLIST_PREFIX}{token}",
                        ttl,
                        "blacklisted"
                    )
            except Exception as e:
                logger.warning(
                    "Failed to blacklist token",
                    extra={"error": str(e)}
                )
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        redis_client = get_redis_client()
        if not redis_client:
            return False
        
        try:
            result = await redis_client.get(f"{TOKEN_BLACKLIST_PREFIX}{token}")
            return result is not None
        except Exception as e:
            logger.warning(
                "Failed to check token blacklist",
                extra={"error": str(e)}
            )
            return False
    
    def _get_user_permissions(self, role: str) -> list[str]:
        """Get user permissions based on role"""
        permission_map = {
            "administrator": [
                "read:all", "write:all", "delete:all",
                "admin:users", "admin:system", "admin:audit",
                "manage:targets", "manage:jobs", "manage:templates"
            ],
            "manager": [
                "read:all", "write:own", "write:team",
                "manage:targets", "manage:jobs", "view:audit"
            ],
            "user": [
                "read:own", "write:own", "execute:jobs"
            ],
            "guest": [
                "read:limited"
            ]
        }
        return permission_map.get(role, ["read:limited"])


class AuthenticationError(Exception):
    """Custom authentication error with enhanced context"""
    
    def __init__(self, message: str, error_code: str = "auth_error", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)