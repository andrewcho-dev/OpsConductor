"""
Auth Service - OpsConductor Authentication Microservice
Handles login, logout, token validation, and session management
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import jwt
import bcrypt
from datetime import datetime, timedelta
import os
import logging

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

# In-memory user store for testing (replace with database later)
USERS_DB = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@opsconductor.com",
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "role": "admin",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    },
    "user": {
        "id": 2,
        "username": "user", 
        "email": "user@opsconductor.com",
        "password_hash": bcrypt.hashpw("user123".encode(), bcrypt.gensalt()).decode(),
        "role": "user",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    },
    "testuser": {
        "id": 3,
        "username": "testuser",
        "email": "testuser@opsconductor.com", 
        "password_hash": bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
        "role": "user",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }
}

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
def create_access_token(user_data: Dict[str, Any]) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    session_id = f"session_{user_data['id']}_{int(datetime.utcnow().timestamp())}"
    
    payload = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "is_active": user_data["is_active"],
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
    
    # Find user
    user = USERS_DB.get(login_request.username)
    if not user:
        logger.warning(f"User not found: {login_request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(login_request.password, user["password_hash"]):
        logger.warning(f"Invalid password for user: {login_request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if user is active
    if not user["is_active"]:
        logger.warning(f"Inactive user login attempt: {login_request.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
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
                "is_active": payload.get("is_active")
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
    """List all users (for testing)"""
    users = []
    for username, user_data in USERS_DB.items():
        users.append({
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data["role"],
            "is_active": user_data["is_active"],
            "created_at": user_data["created_at"]
        })
    return {"users": users}

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