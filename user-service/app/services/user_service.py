"""
User Service Business Logic
"""
import logging
import math
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models.user import UserProfile, UserSettings, UserActivity
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse,
    UserActivityCreate, UserActivityResponse, UserActivityListResponse,
    UserStatsResponse, BulkUserAction, BulkUserActionResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """User service for managing user profiles and settings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (simple implementation)."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, user_data: UserCreate, created_by: str) -> UserResponse:
        """Create a new user profile."""
        try:
            # Check if username already exists (exclude soft-deleted users)
            existing_user = self.db.query(UserProfile).filter(
                and_(
                    UserProfile.username == user_data.username,
                    UserProfile.deleted_at.is_(None)
                )
            ).first()
            if existing_user:
                raise ValueError(f"Username '{user_data.username}' already exists")
            
            # Check if email already exists (exclude soft-deleted users)
            existing_email = self.db.query(UserProfile).filter(
                and_(
                    UserProfile.email == user_data.email,
                    UserProfile.deleted_at.is_(None)
                )
            ).first()
            if existing_email:
                raise ValueError(f"Email '{user_data.email}' already exists")
            
            # Generate user_id (in real implementation, this would come from auth service)
            user_id = f"user-{user_data.username}-{int(datetime.now().timestamp())}"
            
            # Look up the UUID of the creating user
            creating_user = self.db.query(UserProfile).filter(
                UserProfile.user_id == created_by
            ).first()
            created_by_uuid = creating_user.id if creating_user else None
            
            # Hash password
            password_hash = self._hash_password(user_data.password)
            
            # Build full_name from first_name and last_name if not provided
            full_name = user_data.full_name
            if not full_name and (user_data.first_name or user_data.last_name):
                parts = []
                if user_data.first_name:
                    parts.append(user_data.first_name)
                if user_data.last_name:
                    parts.append(user_data.last_name)
                full_name = " ".join(parts) if parts else None
            
            # Create user profile
            db_user = UserProfile(
                user_id=user_id,
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                full_name=full_name,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone=user_data.phone,
                department=user_data.department,
                role=user_data.role,
                permissions=user_data.permissions,
                is_active=user_data.is_active,
                is_verified=user_data.is_verified,
                must_change_password=user_data.must_change_password,
                created_by=created_by_uuid
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            # Create default settings
            self._create_default_settings(user_id)
            
            # Log activity (use the actual user_id from database, not JWT user_id)
            actual_creator_user_id = creating_user.user_id if creating_user else None
            if actual_creator_user_id:
                self._log_activity(
                    user_id=actual_creator_user_id,
                    action="create_user",
                    resource_type="user",
                    resource_id=user_id,
                    details={"username": user_data.username, "role": user_data.role}
                )
            
            logger.info(f"User created: {user_data.username} (ID: {user_id})")
            return UserResponse.from_orm(db_user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by user_id or UUID id."""
        # Try to find by UUID id first, then by user_id (exclude soft-deleted)
        user = self.db.query(UserProfile).filter(
            and_(
                or_(
                    UserProfile.id == user_id,
                    UserProfile.user_id == user_id
                ),
                UserProfile.deleted_at.is_(None)
            )
        ).first()
        
        if user:
            return UserResponse.from_orm(user)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username."""
        user = self.db.query(UserProfile).filter(
            and_(
                UserProfile.username == username,
                UserProfile.deleted_at.is_(None)
            )
        ).first()
        
        if user:
            return UserResponse.from_orm(user)
        return None
    
    def get_users(
        self,
        skip: int = 0,
        limit: int = 25,
        search: Optional[str] = None,
        role: Optional[str] = None,
        active_only: bool = False,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> UserListResponse:
        """Get paginated list of users with filtering."""
        try:
            query = self.db.query(UserProfile)
            
            # Exclude soft-deleted users by default
            query = query.filter(UserProfile.deleted_at.is_(None))
            
            # Apply filters
            if search:
                search_filter = or_(
                    UserProfile.username.ilike(f"%{search}%"),
                    UserProfile.email.ilike(f"%{search}%"),
                    UserProfile.full_name.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            if role:
                query = query.filter(UserProfile.role == role)
            
            if active_only:
                query = query.filter(UserProfile.is_active == True)
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(UserProfile, sort_by, UserProfile.created_at)
            if sort_desc:
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            # Apply pagination
            users = query.offset(skip).limit(limit).all()
            
            # Calculate pagination info
            pages = math.ceil(total / limit) if limit > 0 else 1
            page = (skip // limit) + 1 if limit > 0 else 1
            
            return UserListResponse(
                users=[UserResponse.from_orm(user) for user in users],
                total=total,
                page=page,
                size=limit,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise
    
    def update_user(
        self, 
        user_id: str, 
        user_data: UserUpdate, 
        updated_by: str
    ) -> Optional[UserResponse]:
        """Update user profile."""
        try:
            # Try to find by UUID id first, then by user_id (exclude soft-deleted)
            user = self.db.query(UserProfile).filter(
                and_(
                    or_(
                        UserProfile.id == user_id,
                        UserProfile.user_id == user_id
                    ),
                    UserProfile.deleted_at.is_(None)
                )
            ).first()
            
            if not user:
                return None
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            
            # Build full_name from first_name and last_name if they are being updated
            if 'first_name' in update_data or 'last_name' in update_data:
                first_name = update_data.get('first_name', user.first_name)
                last_name = update_data.get('last_name', user.last_name)
                if first_name or last_name:
                    parts = []
                    if first_name:
                        parts.append(first_name)
                    if last_name:
                        parts.append(last_name)
                    update_data['full_name'] = " ".join(parts) if parts else None
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            # Look up the UUID of the updating user
            updating_user = self.db.query(UserProfile).filter(
                UserProfile.user_id == updated_by
            ).first()
            user.updated_by = updating_user.id if updating_user else None
            
            self.db.commit()
            self.db.refresh(user)
            
            # Log activity (use the actual user_id from database, not JWT user_id)
            actual_updater_user_id = updating_user.user_id if updating_user else None
            if actual_updater_user_id:
                self._log_activity(
                    user_id=actual_updater_user_id,
                    action="update_user",
                    resource_type="user",
                    resource_id=user.user_id,  # Use the actual user_id being updated
                    details=update_data
                )
            
            logger.info(f"User updated: {user.username} (ID: {user_id})")
            return UserResponse.from_orm(user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    def delete_user(self, user_id: str, deleted_by: str) -> bool:
        """Soft delete user profile."""
        try:
            # Try to find by UUID id first, then by user_id (exclude already soft-deleted)
            user = self.db.query(UserProfile).filter(
                and_(
                    or_(
                        UserProfile.id == user_id,
                        UserProfile.user_id == user_id
                    ),
                    UserProfile.deleted_at.is_(None)
                )
            ).first()
            
            if not user:
                return False
            
            username = user.username
            actual_user_id = user.user_id  # Get the actual user_id from the found user
            
            # Look up the deleting user
            deleting_user = self.db.query(UserProfile).filter(
                UserProfile.user_id == deleted_by
            ).first()
            actual_deleter_user_id = deleting_user.user_id if deleting_user else None
            
            # Soft delete user by setting deleted_at timestamp
            user.deleted_at = datetime.utcnow()
            user.updated_by = deleting_user.id if deleting_user else None
            
            # Deactivate user as well
            user.is_active = False
            
            self.db.commit()
            
            # Log activity
            if actual_deleter_user_id:
                self._log_activity(
                    user_id=actual_deleter_user_id,
                    action="delete_user",
                    resource_type="user",
                    resource_id=actual_user_id,
                    details={"username": username, "soft_delete": True}
                )
            
            logger.info(f"User soft deleted: {username} (ID: {user_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error soft deleting user: {e}")
            raise
    
    def get_user_settings(self, user_id: str) -> Optional[UserSettingsResponse]:
        """Get user settings."""
        settings = self.db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()
        
        if settings:
            return UserSettingsResponse.from_orm(settings)
        return None
    
    def update_user_settings(
        self, 
        user_id: str, 
        settings_data: UserSettingsUpdate
    ) -> Optional[UserSettingsResponse]:
        """Update user settings."""
        try:
            settings = self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            
            if not settings:
                # Create settings if they don't exist
                settings = UserSettings(user_id=user_id)
                self.db.add(settings)
            
            # Update fields
            update_data = settings_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(settings, field, value)
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"User settings updated for user: {user_id}")
            return UserSettingsResponse.from_orm(settings)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user settings: {e}")
            raise
    
    def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics (excluding soft-deleted users)."""
        try:
            # Base query excluding soft-deleted users
            base_query = self.db.query(UserProfile).filter(UserProfile.deleted_at.is_(None))
            
            total_users = base_query.count()
            active_users = base_query.filter(
                UserProfile.is_active == True
            ).count()
            inactive_users = total_users - active_users
            admin_users = base_query.filter(
                UserProfile.role == "admin"
            ).count()
            regular_users = total_users - admin_users
            
            # Recent signups (last 7 days)
            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_signups = base_query.filter(
                UserProfile.created_at >= week_ago
            ).count()
            
            return UserStatsResponse(
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users,
                admin_users=admin_users,
                regular_users=regular_users,
                recent_signups=recent_signups
            )
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise
    
    def bulk_user_action(
        self, 
        action_data: BulkUserAction, 
        performed_by: str
    ) -> BulkUserActionResponse:
        """Perform bulk action on users."""
        logger.error(f"=== BULK USER ACTION CALLED ===")
        logger.error(f"Action: {action_data.action}")
        logger.error(f"User IDs: {action_data.user_ids}")
        logger.error(f"Performed by: {performed_by}")
        try:
            success_count = 0
            failed_count = 0
            failed_users = []
            
            logger.info(f"Bulk action request: action={action_data.action}, user_ids={action_data.user_ids}")
            
            # Look up the performing user for updated_by field
            performing_user = self.db.query(UserProfile).filter(
                UserProfile.user_id == performed_by
            ).first()
            
            for user_id in action_data.user_ids:
                try:
                    logger.info(f"Processing bulk action '{action_data.action}' for user_id: {user_id}")
                    # For bulk actions, we need to find users even if soft-deleted
                    # (in case we want to reactivate them)
                    user = self.db.query(UserProfile).filter(
                        or_(
                            UserProfile.id == user_id,
                            UserProfile.user_id == user_id
                        )
                    ).first()
                    
                    if not user:
                        logger.error(f"User not found for ID: {user_id}")
                        failed_count += 1
                        failed_users.append(user_id)
                        continue
                    
                    logger.info(f"Found user: {user.username} (id={user.id}, user_id={user.user_id})")
                    
                    if action_data.action == "activate":
                        user.is_active = True
                        user.deleted_at = None  # Undelete if reactivating
                        user.updated_by = performing_user.id if performing_user else None
                    elif action_data.action == "deactivate":
                        user.is_active = False
                        user.updated_by = performing_user.id if performing_user else None
                    elif action_data.action == "delete":
                        # Soft delete: set deleted_at timestamp and deactivate
                        logger.info(f"Before soft delete: user.deleted_at={user.deleted_at}, user.is_active={user.is_active}")
                        user.deleted_at = datetime.utcnow()
                        user.is_active = False
                        user.updated_by = performing_user.id if performing_user else None
                        logger.info(f"After soft delete: user.deleted_at={user.deleted_at}, user.is_active={user.is_active}")
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing user {user_id}: {e}")
                    failed_count += 1
                    failed_users.append(user_id)
            
            self.db.commit()
            
            # Log activity (don't let activity logging failure affect the main operation)
            try:
                self._log_activity(
                    user_id=performed_by,
                    action=f"bulk_{action_data.action}",
                    resource_type="user",
                    resource_id="bulk",
                    details={
                        "user_count": len(action_data.user_ids),
                        "success_count": success_count,
                        "failed_count": failed_count
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log bulk action activity: {e}")
            
            return BulkUserActionResponse(
                success_count=success_count,
                failed_count=failed_count,
                failed_users=failed_users,
                message=f"Bulk {action_data.action} completed: {success_count} successful, {failed_count} failed"
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error performing bulk action: {e}")
            raise
    
    def _create_default_settings(self, user_id: str):
        """Create default settings for a user."""
        try:
            settings = UserSettings(
                user_id=user_id,
                preferences={"dashboard_layout": "default", "items_per_page": 25},
                timezone="UTC",
                theme="light",
                language="en",
                notifications_enabled=True
            )
            self.db.add(settings)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating default settings for user {user_id}: {e}")
    
    def _log_activity(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log user activity."""
        try:
            # Check if the user exists before logging activity
            user_exists = self.db.query(UserProfile).filter(
                or_(
                    UserProfile.id == user_id,
                    UserProfile.user_id == user_id
                )
            ).first()
            
            if not user_exists:
                logger.warning(f"Cannot log activity for non-existent user: {user_id}")
                return
                
            activity = UserActivity(
                user_id=user_exists.user_id,  # Use the actual user_id from the database
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(activity)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            self.db.rollback()
    
    def get_user_activity(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> UserActivityListResponse:
        """Get user activity history."""
        try:
            # First, get the actual user_id from the database (in case UUID was passed)
            user = self.db.query(UserProfile).filter(
                or_(
                    UserProfile.id == user_id,
                    UserProfile.user_id == user_id
                )
            ).first()
            
            if not user:
                return UserActivityListResponse(
                    activities=[],
                    total=0,
                    page=1,
                    size=limit,
                    pages=0
                )
            
            # Use the actual user_id for activity lookup
            actual_user_id = user.user_id
            
            # Query activities
            query = self.db.query(UserActivity).filter(
                UserActivity.user_id == actual_user_id
            )
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            activities = query.order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()
            
            # Calculate pagination info
            pages = math.ceil(total / limit) if limit > 0 else 1
            page = (skip // limit) + 1 if limit > 0 else 1
            
            # Convert to response objects
            activity_responses = []
            for activity in activities:
                activity_dict = activity.to_dict()
                activity_responses.append(UserActivityResponse(**activity_dict))
            
            return UserActivityListResponse(
                activities=activity_responses,
                total=total,
                page=page,
                size=limit,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return UserActivityListResponse(
                activities=[],
                total=0,
                page=1,
                size=limit,
                pages=0
            )