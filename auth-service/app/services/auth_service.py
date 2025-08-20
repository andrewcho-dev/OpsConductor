from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

from app.models.user import User
from app.core.security import verify_password, create_session_token, decode_token
from app.core.session_manager import session_manager
from app.schemas.auth import UserInfo, TokenValidationResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            User object if authentication successful, None otherwise
        """
        logger.debug(f"Attempting to authenticate user '{username}'")
        user = db.query(User).filter(User.username == username).first()
        
        # Authentication failure - user not found
        if not user:
            logger.debug(f"User '{username}' not found")
            return None
        

        
        logger.debug(f"User found, verifying password")
        
        # Authentication failure - invalid password
        if not verify_password(password, user.password_hash):
            logger.debug(f"Password verification failed for user '{username}'")
            return None
        
        logger.debug(f"Authentication successful for user '{username}'")
        return user

    @staticmethod
    async def create_user_session(db: Session, user: User, client_ip: str = None, user_agent: str = None) -> Dict[str, str]:
        """
        Create a new user session and return session token.
        
        Args:
            db: Database session
            user: Authenticated user
            client_ip: IP address of the client
            user_agent: User agent of the client
            
        Returns:
            Dictionary containing access_token, session_id, and token_type
        """
        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        # Create session data
        user_data = {
            "username": user.username,
            "role": user.role,  # Include role for JWT token
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        
        # Create session in Redis
        session_id = await session_manager.create_session(user.id, user_data)
        
        # Create JWT token with session ID and user data
        access_token = create_session_token(user.id, session_id, user_data)
        
        return {
            "access_token": access_token,
            "session_id": session_id,
            "token_type": "bearer"
        }

    @staticmethod
    async def validate_token(token: str) -> TokenValidationResponse:
        """
        Validate session token and return user information.
        
        Args:
            token: JWT token to validate
            
        Returns:
            TokenValidationResponse with validation result
        """
        try:
            # Decode JWT token
            payload = decode_token(token)
            if not payload:
                return TokenValidationResponse(
                    valid=False,
                    error="Invalid token format"
                )
            
            session_id = payload.get("session_id")
            user_id = payload.get("user_id")
            
            if not session_id or not user_id:
                return TokenValidationResponse(
                    valid=False,
                    error="Missing session or user information"
                )
            
            # Check if session is still valid in Redis
            session_data = await session_manager.get_session(session_id)
            if not session_data:
                return TokenValidationResponse(
                    valid=False,
                    error="Session expired or not found"
                )
            
            # Verify user_id matches
            if session_data.get("user_id") != user_id:
                return TokenValidationResponse(
                    valid=False,
                    error="Session user mismatch"
                )
            
            # Update activity (this extends the session)
            await session_manager.update_activity(session_id)
            
            # Create user info from session data
            user_data = session_data.get("user_data", {})
            user_info = UserInfo(
                id=user_id,
                username=user_data.get("username", ""),
                last_login=None
            )
            
            return TokenValidationResponse(
                valid=True,
                user=user_info,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return TokenValidationResponse(
                valid=False,
                error="Token validation failed"
            )

    @staticmethod
    async def destroy_session(session_id: str) -> bool:
        """
        Destroy a user session.
        
        Args:
            session_id: ID of the session to destroy
            
        Returns:
            True if session was destroyed successfully
        """
        return await session_manager.destroy_session(session_id)

    @staticmethod
    async def get_session_status(session_id: str) -> Dict[str, Any]:
        """
        Get session status.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary with session status information
        """
        return await session_manager.get_session_status(session_id)

    @staticmethod
    async def extend_session(session_id: str) -> bool:
        """
        Extend user session.
        
        Args:
            session_id: ID of the session to extend
            
        Returns:
            True if session was extended successfully
        """
        return await session_manager.extend_session(session_id)