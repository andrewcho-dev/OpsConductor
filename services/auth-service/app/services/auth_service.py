"""
Auth Service - Core authentication logic
Handles JWT tokens, sessions, login/logout - calls user-service for user data
"""

import hashlib
import secrets
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import get_db
from app.models.auth import AuthSession, BlacklistedToken, LoginAttempt, PasswordResetToken
from app.schemas.auth import LoginRequest, LoginResponse, TokenValidationResponse

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service - integrates with user-service"""
    
    def __init__(self):
        self.user_service_url = settings.USER_SERVICE_URL.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return secrets.token_urlsafe(32)
    
    async def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user from user-service by email"""
        try:
            response = await self.client.get(
                f"{self.user_service_url}/api/v1/users/by-email/{email}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    
    async def _verify_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify password with user-service"""
        try:
            response = await self.client.post(
                f"{self.user_service_url}/api/v1/auth/verify-password",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error verifying password: {e}")
            return None
    
    def _create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user_data["id"]),
            "email": user_data["email"],
            "user_id": user_data["id"],
            "roles": [role["name"] for role in user_data.get("roles", [])],
            "permissions": user_data.get("permissions", []),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def _create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    async def login(self, login_data: LoginRequest, ip_address: str, user_agent: str, db: Session) -> LoginResponse:
        """Authenticate user and create session"""
        
        # Check rate limiting
        recent_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.email == login_data.email,
            LoginAttempt.attempted_at > datetime.utcnow() - timedelta(minutes=15)
        ).count()
        
        if recent_attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Verify credentials with user-service
        user_data = await self._verify_password(login_data.email, login_data.password)
        
        # Log attempt
        attempt = LoginAttempt(
            email=login_data.email,
            ip_address=ip_address,
            success=user_data is not None,
            user_agent=user_agent,
            failure_reason=None if user_data else "invalid_credentials"
        )
        db.add(attempt)
        
        if not user_data:
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user_data.get("is_active"):
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Create tokens
        access_token = self._create_access_token(user_data)
        refresh_token = self._create_refresh_token(user_data["id"]) if login_data.remember_me else None
        
        # Create session
        session_id = self._generate_session_id()
        expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        session = AuthSession(
            session_id=session_id,
            user_id=user_data["id"],
            token_hash=self._hash_token(access_token),
            refresh_token_hash=self._hash_token(refresh_token) if refresh_token else None,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)
        db.commit()
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_data
        )
    
    async def validate_token(self, token: str, db: Session) -> TokenValidationResponse:
        """Validate JWT token"""
        try:
            # Check if token is blacklisted
            token_hash = self._hash_token(token)
            blacklisted = db.query(BlacklistedToken).filter(
                BlacklistedToken.token_hash == token_hash,
                BlacklistedToken.expires_at > datetime.utcnow()
            ).first()
            
            if blacklisted:
                return TokenValidationResponse(valid=False)
            
            # Decode JWT
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = int(payload.get("sub"))
            
            if not user_id:
                return TokenValidationResponse(valid=False)
            
            # Check if session exists and is active
            session = db.query(AuthSession).filter(
                AuthSession.user_id == user_id,
                AuthSession.token_hash == token_hash,
                AuthSession.is_active == True,
                AuthSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return TokenValidationResponse(valid=False)
            
            # Update last accessed
            session.last_accessed_at = datetime.utcnow()
            db.commit()
            
            # Get fresh user data from user-service
            user_data = await self._get_user_by_email(payload.get("email"))
            if not user_data or not user_data.get("is_active"):
                return TokenValidationResponse(valid=False)
            
            return TokenValidationResponse(
                valid=True,
                user=user_data,
                permissions=user_data.get("permissions", []),
                roles=[role["name"] for role in user_data.get("roles", [])],
                expires_at=datetime.fromtimestamp(payload.get("exp"))
            )
            
        except JWTError:
            return TokenValidationResponse(valid=False)
        except Exception as e:
            print(f"Token validation error: {e}")
            return TokenValidationResponse(valid=False)
    
    async def logout(self, token: str, all_sessions: bool, db: Session) -> bool:
        """Logout user and invalidate tokens"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = int(payload.get("sub"))
            token_hash = self._hash_token(token)
            
            if all_sessions:
                # Deactivate all sessions for user
                db.query(AuthSession).filter(
                    AuthSession.user_id == user_id,
                    AuthSession.is_active == True
                ).update({"is_active": False})
            else:
                # Deactivate specific session
                db.query(AuthSession).filter(
                    AuthSession.user_id == user_id,
                    AuthSession.token_hash == token_hash
                ).update({"is_active": False})
            
            # Blacklist the token
            expires_at = datetime.fromtimestamp(payload.get("exp"))
            blacklisted = BlacklistedToken(
                token_hash=token_hash,
                user_id=user_id,
                expires_at=expires_at,
                reason="logout"
            )
            db.add(blacklisted)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"Logout error: {e}")
            return False
    
    async def get_user_sessions(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get active sessions for user"""
        sessions = db.query(AuthSession).filter(
            AuthSession.user_id == user_id,
            AuthSession.is_active == True,
            AuthSession.expires_at > datetime.utcnow()
        ).all()
        
        return [
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "last_accessed_at": session.last_accessed_at,
                "ip_address": str(session.ip_address) if session.ip_address else None,
                "user_agent": session.user_agent,
                "expires_at": session.expires_at
            }
            for session in sessions
        ]