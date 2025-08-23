"""
Auth Service - OpsConductor Authentication Microservice
Handles login, logout, token validation, and session management
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import jwt
import bcrypt
from datetime import datetime, timedelta
import os
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpsConductor Auth Service", 
    description="Authentication and session management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "opsconductor-super-secret-key-for-auth-2025")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    "admin": [
        "users:create", "users:read", "users:update", "users:delete", "users:manage_roles",
        "targets:create", "targets:read", "targets:update", "targets:delete",
        "jobs:create", "jobs:read", "jobs:update", "jobs:delete", "jobs:execute",
        "system:admin", "audit:read"
    ],
    "user": [
        "users:read",  # Can read user info (limited)
        "targets:read", "jobs:read"  # Basic read permissions
    ]
}

# Note: User data is now managed by the user-service
# Authentication is handled via API calls to user-service

# In-memory session store
ACTIVE_SESSIONS = {}

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenValidationRequest(BaseModel):
    token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    expires_at: str

class TokenValidationResponse(BaseModel):
    valid: bool
    user: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None

# Helper functions
def get_user_permissions(role: str) -> List[str]:
    """Get permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, [])

def create_access_token(user_data: Dict[str, Any]) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    session_id = f"session_{user_data['id']}_{int(datetime.utcnow().timestamp())}"
    
    # Use permissions from user service, fallback to role-based if not available
    permissions = user_data.get("permissions", get_user_permissions(user_data["role"]))
    
    payload = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "is_active": user_data["is_active"],
        "permissions": permissions,
        "session_id": session_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access_token"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Store session
    ACTIVE_SESSIONS[session_id] = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "token": token
    }
    
    return token

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        session_id = payload.get("session_id")
        
        # Check if session exists and is active
        if session_id and session_id in ACTIVE_SESSIONS:
            # Update last activity
            ACTIVE_SESSIONS[session_id]["last_activity"] = datetime.utcnow()
            return payload
        else:
            logger.warning(f"Session {session_id} not found in active sessions")
            return None
            
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}

@app.get("/api/v1/info")
async def service_info():
    """Service information"""
    return {
        "service": "auth-service",
        "version": "1.0.0", 
        "description": "OpsConductor Authentication Service",
        "status": "running",
        "active_sessions": len(ACTIVE_SESSIONS)
    }

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """User login endpoint"""
    logger.info(f"Login attempt for user: {login_request.username}")
    
    try:
        # Authenticate via user service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{USER_SERVICE_URL}/api/v1/users/authenticate",
                json={"username": login_request.username, "password": login_request.password},
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.warning(f"User service authentication failed for: {login_request.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )
            
            result = response.json()
            if not result.get("success"):
                logger.warning(f"Authentication failed for user: {login_request.username} - {result.get('message')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get("message", "Invalid username or password")
                )
            
            user = result.get("user")
            if not user:
                logger.error(f"No user data returned from user service for: {login_request.username}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication service error"
                )
    
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to user service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )
    
    # Create access token
    access_token = create_access_token(user)
    expires_at = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    
    logger.info(f"Login successful for user: {login_request.username}")
    
    return LoginResponse(
        access_token=access_token,
        user={
            "id": user["id"],
            "username": user["username"], 
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"]
        },
        expires_at=expires_at
    )

@app.post("/api/v1/auth/validate", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest):
    """Token validation endpoint"""
    logger.info(f"Token validation request: {request.token[:50]}...")
    
    payload = verify_token(request.token)
    
    if payload:
        logger.info(f"Token valid for user: {payload.get('username')}")
        return TokenValidationResponse(
            valid=True,
            user={
                "id": payload.get("user_id"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "is_active": payload.get("is_active"),
                "permissions": payload.get("permissions", [])
            },
            session_id=payload.get("session_id")
        )
    else:
        logger.warning("Token validation failed")
        return TokenValidationResponse(
            valid=False,
            error="Invalid or expired token"
        )

@app.post("/api/v1/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout endpoint"""
    token = credentials.credentials
    logger.info(f"Logout request: {token[:50]}...")
    
    payload = verify_token(token)
    if payload:
        session_id = payload.get("session_id")
        if session_id in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[session_id]
            logger.info(f"Session {session_id} terminated")
        
        return {"message": "Logout successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/api/v1/auth/session/status")
async def get_session_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get session status"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload:
        session_id = payload.get("session_id")
        session = ACTIVE_SESSIONS.get(session_id)
        
        if session:
            return {
                "active": True,
                "user": {
                    "id": payload.get("user_id"),
                    "username": payload.get("username"),
                    "role": payload.get("role")
                },
                "session_id": session_id,
                "last_activity": session["last_activity"].isoformat(),
                "expires_at": datetime.fromtimestamp(payload.get("exp")).isoformat()
            }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid session"
    )

@app.post("/api/v1/auth/session/extend")
async def extend_session(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extend session"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload:
        # For now, just update last activity (session is automatically extended)
        return {"message": "Session extended"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/api/v1/auth/users")
async def list_users():
    """List all users (proxy to user service)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/v1/users/",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch users from user service"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to user service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )

@app.get("/api/v1/auth/sessions")
async def list_active_sessions():
    """List active sessions (for testing)"""
    sessions = []
    for session_id, session in ACTIVE_SESSIONS.items():
        sessions.append({
            "session_id": session_id,
            "user_id": session["user_id"],
            "username": session["username"],
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat()
        })
    return {"active_sessions": sessions, "total": len(sessions)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")