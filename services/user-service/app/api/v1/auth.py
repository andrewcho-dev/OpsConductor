"""
User Service Auth Endpoints
Provides authentication support for auth-service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordVerificationRequest(BaseModel):
    """Password verification request"""
    email: EmailStr
    password: str

class PasswordVerificationResponse(BaseModel):
    """Password verification response"""
    valid: bool
    user: dict = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/verify-password", response_model=dict)
async def verify_user_password(
    request: PasswordVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify user password for authentication
    Used by auth-service during login
    """
    # Get user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has a password (some users might use SSO only)
    if not hasattr(user, 'password_hash') or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a password set"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Return user data for token creation
    return {
        "id": user.id,
        "user_uuid": str(user.user_uuid),
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_superuser": user.is_superuser,
        "roles": [
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name
            }
            for role in user.roles if role.is_active
        ],
        "permissions": user.permissions,  # This uses the @property from the model
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
    }