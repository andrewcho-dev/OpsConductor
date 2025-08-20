"""
Comprehensive user service for managing all user operations.
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from app.models.user import User, UserSession, PasswordHistory, UserAuditLog
from app.core.security import get_password_hash, verify_password
from app.services.config_service import ConfigService
from app.schemas.user import UserCreate, UserUpdate, UserPasswordUpdate, BulkUserAction


class UserService:
    """Comprehensive service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
    
    # User CRUD Operations
    def create_user(self, user_data: UserCreate, created_by: Optional[int] = None) -> User:
        """Create a new user with comprehensive validation and setup."""
        # Validate password strength
        password_validation = self.config_service.validate_password_strength(user_data.password)
        if not password_validation["valid"]:
            raise ValueError(f"Password validation failed: {', '.join(password_validation['errors'])}")
        
        # Check for existing username/email
        if self.get_user_by_username(user_data.username):
            raise ValueError("Username already exists")
        
        if self.get_user_by_email(user_data.email):
            raise ValueError("Email already exists")
        
        password_hash = get_password_hash(user_data.password)
        
        # Calculate password expiry if enabled
        password_expires_at = None
        expiry_days = self.config_service.get_config("password.expiry_days")
        if expiry_days and expiry_days > 0:
            password_expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            department=user_data.department,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            must_change_password=user_data.must_change_password,
            password_expires_at=password_expires_at,
            created_by=created_by
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Add to password history
        self._add_password_history(user.id, password_hash)
        
        # Log user creation
        self._log_audit_event(
            user_id=user.id,
            event_type="user_created",
            event_description=f"User {user.username} created",
            event_metadata={"created_by": created_by, "role": user.role}
        )
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False,
        role: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> Tuple[List[User], int]:
        """Get paginated list of users with filtering and search."""
        query = self.db.query(User)
        
        # Apply filters
        if active_only:
            query = query.filter(User.is_active == True)
        
        if role:
            query = query.filter(User.role == role)
        
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if hasattr(User, sort_by):
            order_column = getattr(User, sort_by)
            if sort_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    def update_user(self, user_id: int, user_data: UserUpdate, updated_by: Optional[int] = None) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Check for email conflicts
        if user_data.email and user_data.email != user.email:
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already exists")
        
        # Track changes for audit
        changes = {}
        for field, value in user_data.dict(exclude_unset=True).items():
            if hasattr(user, field) and getattr(user, field) != value:
                changes[field] = {"old": getattr(user, field), "new": value}
                setattr(user, field, value)
        
        if changes:
            self.db.commit()
            self.db.refresh(user)
            
            # Log changes
            self._log_audit_event(
                user_id=user.id,
                event_type="user_updated",
                event_description=f"User {user.username} updated",
                event_metadata={"changes": changes, "updated_by": updated_by}
            )
        
        return user
    
    def delete_user(self, user_id: int, deleted_by: Optional[int] = None) -> bool:
        """Delete a user (soft delete by deactivating)."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Deactivate instead of hard delete
        user.is_active = False
        self.db.commit()
        
        # Terminate all sessions
        self._terminate_all_user_sessions(user_id, "account_deleted")
        
        # Log deletion
        self._log_audit_event(
            user_id=user.id,
            event_type="user_deleted",
            event_description=f"User {user.username} deleted",
            event_metadata={"deleted_by": deleted_by}
        )
        
        return True
    
    # Authentication and Security
    def authenticate_user(self, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[User]:
        """Authenticate user with comprehensive security checks."""
        user = self.get_user_by_username(username) or self.get_user_by_email(username)
        
        if not user:
            self._log_audit_event(
                event_type="login_failed",
                event_description=f"Login attempt with non-existent username: {username}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        # Check if account is locked
        if self._is_account_locked(user):
            self._log_audit_event(
                user_id=user.id,
                event_type="login_failed_locked",
                event_description=f"Login attempt on locked account: {username}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            self._handle_failed_login(user, ip_address, user_agent)
            return None
        
        # Check if account is active
        if not user.is_active:
            self._log_audit_event(
                user_id=user.id,
                event_type="login_failed_inactive",
                event_description=f"Login attempt on inactive account: {username}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        # Successful login - reset failed attempts and update login info
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        
        self.db.commit()
        
        # Log successful login
        self._log_audit_event(
            user_id=user.id,
            event_type="login_success",
            event_description=f"Successful login: {username}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user
    
    def change_password(self, user_id: int, password_data: UserPasswordUpdate, changed_by: Optional[int] = None) -> bool:
        """Change user password with policy validation."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password if provided (not required for admin resets)
        if password_data.current_password and not verify_password(password_data.current_password, user.password_hash):
            return False
        
        # Validate new password strength
        password_validation = self.config_service.validate_password_strength(password_data.new_password)
        if not password_validation["valid"]:
            raise ValueError(f"Password validation failed: {', '.join(password_validation['errors'])}")
        
        # Check password history
        if self._is_password_in_history(user_id, password_data.new_password):
            history_count = self.config_service.get_config("password.history_count") or 5
            raise ValueError(f"Password cannot be one of the last {history_count} passwords used")
        
        # Check minimum password age
        min_age_hours = self.config_service.get_config("password.min_age_hours") or 0
        if min_age_hours > 0 and user.last_password_change:
            min_change_time = user.last_password_change + timedelta(hours=min_age_hours)
            if datetime.utcnow() < min_change_time:
                raise ValueError(f"Password cannot be changed for {min_age_hours} hours after last change")
        
        # Update password
        new_password_hash = get_password_hash(password_data.new_password)
        user.password_hash = new_password_hash
        user.last_password_change = datetime.utcnow()
        user.password_changed_at = datetime.utcnow()
        
        # Set expiry if enabled
        expiry_days = self.config_service.get_config("password.expiry_days")
        if expiry_days and expiry_days > 0:
            user.password_expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        # Clear must change password flag if set
        if password_data.force_change:
            user.must_change_password = False
        
        self.db.commit()
        
        # Add to password history
        self._add_password_history(user_id, new_password_hash)
        
        # Log password change
        self._log_audit_event(
            user_id=user.id,
            event_type="password_changed",
            event_description=f"Password changed for user {user.username}",
            event_metadata={"changed_by": changed_by, "forced": password_data.force_change}
        )
        
        return True
    
    # Bulk Operations
    def bulk_user_action(self, action_data: BulkUserAction, performed_by: Optional[int] = None) -> Dict[str, Any]:
        """Perform bulk actions on multiple users."""
        successful = []
        failed = []
        
        for user_id in action_data.user_ids:
            try:
                user = self.get_user_by_id(user_id)
                if not user:
                    failed.append({"user_id": user_id, "error": "User not found"})
                    continue
                
                if action_data.action == "activate":
                    user.is_active = True
                elif action_data.action == "deactivate":
                    user.is_active = False
                elif action_data.action == "lock":
                    user.is_locked = True
                    user.locked_until = datetime.utcnow() + timedelta(hours=24)  # Default 24h lock
                elif action_data.action == "unlock":
                    user.is_locked = False
                    user.locked_until = None
                    user.failed_login_attempts = 0
                elif action_data.action == "force_password_change":
                    user.must_change_password = True
                elif action_data.action == "delete":
                    user.is_active = False
                
                self.db.commit()
                successful.append(user_id)
                
                # Log action
                self._log_audit_event(
                    user_id=user.id,
                    event_type=f"bulk_{action_data.action}",
                    event_description=f"Bulk {action_data.action} performed on user {user.username}",
                    event_metadata={"performed_by": performed_by, "reason": action_data.reason}
                )
                
            except Exception as e:
                failed.append({"user_id": user_id, "error": str(e)})
        
        return {
            "successful": successful,
            "failed": failed,
            "total_processed": len(action_data.user_ids)
        }
    
    # User Statistics and Analytics
    def get_user_stats(self) -> Dict[str, int]:
        """Get comprehensive user statistics."""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        locked_users = self.db.query(User).filter(User.is_locked == True).count()
        unverified_users = self.db.query(User).filter(User.is_verified == False).count()
        users_requiring_password_change = self.db.query(User).filter(User.must_change_password == True).count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logins = self.db.query(UserAuditLog).filter(
            and_(
                UserAuditLog.event_type == "login_success",
                UserAuditLog.created_at >= yesterday
            )
        ).count()
        
        failed_attempts = self.db.query(UserAuditLog).filter(
            and_(
                UserAuditLog.event_type.like("login_failed%"),
                UserAuditLog.created_at >= yesterday
            )
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "locked_users": locked_users,
            "unverified_users": unverified_users,
            "users_requiring_password_change": users_requiring_password_change,
            "recent_logins_24h": recent_logins,
            "failed_attempts_24h": failed_attempts
        }
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """Get detailed user activity information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Get active sessions
        active_sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        # Get recent activity
        recent_activity = self.db.query(UserAuditLog).filter(
            UserAuditLog.user_id == user_id
        ).order_by(desc(UserAuditLog.created_at)).limit(limit).all()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "last_login": user.last_login,
            "last_login_ip": user.last_login_ip,
            "active_sessions": active_sessions,
            "failed_attempts": user.failed_login_attempts,
            "is_locked": user.is_locked,
            "locked_until": user.locked_until,
            "recent_activity": recent_activity
        }
    
    # Private helper methods
    def _is_account_locked(self, user: User) -> bool:
        """Check if account is currently locked."""
        if not user.is_locked:
            return False
        
        if user.locked_until and datetime.utcnow() > user.locked_until:
            # Lock has expired, unlock the account
            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0
            self.db.commit()
            return False
        
        return True
    
    def _handle_failed_login(self, user: User, ip_address: Optional[str], user_agent: Optional[str]):
        """Handle failed login attempt."""
        user.failed_login_attempts += 1
        
        max_attempts = self.config_service.get_config("security.max_failed_attempts") or 5
        lockout_duration = self.config_service.get_config("security.lockout_duration_minutes") or 30
        
        if user.failed_login_attempts >= max_attempts:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration)
            
            self._log_audit_event(
                user_id=user.id,
                event_type="account_locked",
                event_description=f"Account locked due to {max_attempts} failed login attempts",
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        self.db.commit()
        
        self._log_audit_event(
            user_id=user.id,
            event_type="login_failed",
            event_description=f"Failed login attempt ({user.failed_login_attempts}/{max_attempts})",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def _add_password_history(self, user_id: int, password_hash: str):
        """Add password to history and maintain history limit."""
        history_count = self.config_service.get_config("password.history_count") or 5
        
        # Add new password to history
        password_history = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash
        )
        self.db.add(password_history)
        
        # Remove old entries beyond history limit
        old_entries = self.db.query(PasswordHistory).filter(
            PasswordHistory.user_id == user_id
        ).order_by(desc(PasswordHistory.created_at)).offset(history_count).all()
        
        for entry in old_entries:
            self.db.delete(entry)
        
        self.db.commit()
    
    def _is_password_in_history(self, user_id: int, password: str) -> bool:
        """Check if password exists in user's password history."""
        history_entries = self.db.query(PasswordHistory).filter(
            PasswordHistory.user_id == user_id
        ).all()
        
        for entry in history_entries:
            if verify_password(password, entry.password_hash):
                return True
        
        return False
    
    def _terminate_all_user_sessions(self, user_id: int, reason: str = "admin_action"):
        """Terminate all active sessions for a user."""
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).all()
        
        for session in sessions:
            session.is_active = False
            session.logout_reason = reason
        
        self.db.commit()
    
    def _log_audit_event(
        self, 
        event_type: str, 
        event_description: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        event_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log audit event."""
        audit_log = UserAuditLog(
            user_id=user_id,
            event_type=event_type,
            event_description=event_description,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            event_metadata=event_metadata
        )
        
        self.db.add(audit_log)
        self.db.commit()