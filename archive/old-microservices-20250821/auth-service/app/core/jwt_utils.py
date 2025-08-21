"""
JWT token utilities for Auth Service
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)


class JWTManager:
    """JWT token management"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(
        self,
        user_id: int,
        user_data: Dict[str, Any],
        session_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Create token payload
            payload = {
                "sub": str(user_id),  # Subject (user ID)
                "session_id": session_id,
                "user_data": user_data,
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": str(uuid4()),  # JWT ID for token tracking
                "type": "access"
            }
            
            # Encode token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Access token created for user {user_id}, expires at {expire}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def create_refresh_token(
        self,
        user_id: int,
        session_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            # Create token payload (minimal for refresh tokens)
            payload = {
                "sub": str(user_id),
                "session_id": session_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": str(uuid4()),
                "type": "refresh"
            }
            
            # Encode token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Refresh token created for user {user_id}, expires at {expire}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Validate token type
            token_type = payload.get("type")
            if token_type not in ["access", "refresh"]:
                logger.warning(f"Invalid token type: {token_type}")
                return None
            
            # Extract user ID
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Token missing user ID")
                return None
            
            # Extract session ID
            session_id = payload.get("session_id")
            if not session_id:
                logger.warning("Token missing session ID")
                return None
            
            logger.info(f"Token verified for user {user_id}, session {session_id}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for debugging/logging)"""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiry time"""
        try:
            payload = self.decode_token_without_verification(token)
            if payload and "exp" in payload:
                return datetime.fromtimestamp(payload["exp"])
            return None
        except Exception as e:
            logger.error(f"Failed to get token expiry: {e}")
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired"""
        try:
            expiry = self.get_token_expiry(token)
            if expiry:
                return datetime.utcnow() > expiry
            return True
        except Exception as e:
            logger.error(f"Failed to check token expiry: {e}")
            return True
    
    def refresh_access_token(
        self,
        refresh_token: str,
        user_data: Dict[str, Any]
    ) -> Optional[str]:
        """Create new access token from refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid refresh token")
                return None
            
            user_id = int(payload.get("sub"))
            session_id = payload.get("session_id")
            
            # Create new access token
            new_access_token = self.create_access_token(
                user_id=user_id,
                user_data=user_data,
                session_id=session_id
            )
            
            logger.info(f"Access token refreshed for user {user_id}")
            return new_access_token
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return None


# Global JWT manager instance
jwt_manager = JWTManager()