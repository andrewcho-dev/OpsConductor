"""
User Management Query Handlers
"""
from typing import List, Optional

from app.shared.infrastructure.cqrs import QueryHandler, QueryResult, query_handler
from app.domains.user_management.queries.user_queries import (
    GetUserByIdQuery, GetUserByUsernameQuery, GetUserByEmailQuery,
    GetUsersQuery, GetActiveUsersQuery, GetUsersByRoleQuery
)
from app.domains.user_management.services.user_domain_service import UserDomainService
from app.models.user_models import User
from app.shared.infrastructure.container import inject
from app.shared.exceptions.base import ENABLEDRMException


def _serialize_user(user: User) -> dict:
    """Serialize user object to dictionary."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }


@query_handler(GetUserByIdQuery)
class GetUserByIdQueryHandler(QueryHandler[GetUserByIdQuery, QueryResult]):
    """Handler for getting user by ID."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, query: GetUserByIdQuery) -> QueryResult:
        """Handle get user by ID query."""
        try:
            user = await user_service.get_user_by_id(query.user_id)
            return QueryResult(data=_serialize_user(user))
        except ENABLEDRMException:
            return QueryResult(data=None)


@query_handler(GetUserByUsernameQuery)
class GetUserByUsernameQueryHandler(QueryHandler[GetUserByUsernameQuery, QueryResult]):
    """Handler for getting user by username."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, query: GetUserByUsernameQuery) -> QueryResult:
        """Handle get user by username query."""
        try:
            user = await user_service.user_repository.get_by_username(query.username)
            return QueryResult(data=_serialize_user(user) if user else None)
        except ENABLEDRMException:
            return QueryResult(data=None)


@query_handler(GetUserByEmailQuery)
class GetUserByEmailQueryHandler(QueryHandler[GetUserByEmailQuery, QueryResult]):
    """Handler for getting user by email."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, query: GetUserByEmailQuery) -> QueryResult:
        """Handle get user by email query."""
        try:
            user = await user_service.user_repository.get_by_email(query.email)
            return QueryResult(data=_serialize_user(user) if user else None)
        except ENABLEDRMException:
            return QueryResult(data=None)


@query_handler(GetUsersQuery)
class GetUsersQueryHandler(QueryHandler[GetUsersQuery, QueryResult]):
    """Handler for getting users with pagination and filtering."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, query: GetUsersQuery) -> QueryResult:
        """Handle get users query."""
        try:
            users = await user_service.get_users(
                skip=query.skip,
                limit=query.limit,
                role=query.role,
                active_only=query.active_only
            )
            
            # Get total count for pagination
            total_count = await user_service.user_repository.count()
            
            serialized_users = [_serialize_user(user) for user in users]
            
            return QueryResult(
                data=serialized_users,
                total_count=total_count,
                page=query.skip // query.limit + 1,
                page_size=query.limit,
                has_next=(query.skip + query.limit) < total_count,
                has_previous=query.skip > 0
            )
        except ENABLEDRMException:
            return QueryResult(data=[])


@query_handler(GetActiveUsersQuery)
class GetActiveUsersQueryHandler(QueryHandler[GetActiveUsersQuery, QueryResult]):
    """Handler for getting active users."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, query: GetActiveUsersQuery) -> QueryResult:
        """Handle get active users query."""
        try:
            users = await user_service.user_repository.get_active_users(
                skip=query.skip,
                limit=query.limit
            )
            
            # Get total count of active users
            total_count = await user_service.user_repository.count({"is_active": True})
            
            serialized_users = [_serialize_user(user) for user in users]
            
            return QueryResult(
                data=serialized_users,
                total_count=total_count,
                page=query.skip // query.limit + 1,
                page_size=query.limit,
                has_next=(query.skip + query.limit) < total_count,
                has_previous=query.skip > 0
            )
        except ENABLEDRMException:
            return QueryResult(data=[])


@query_handler(GetUsersByRoleQuery)
class GetUsersByRoleQueryHandler(QueryHandler[GetUsersByRoleQuery, QueryResult]):
    """Handler for getting users by role."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, query: GetUsersByRoleQuery) -> QueryResult:
        """Handle get users by role query."""
        try:
            users = await user_service.user_repository.get_by_role(
                role=query.role,
                skip=query.skip,
                limit=query.limit
            )
            
            # Get total count for this role
            total_count = await user_service.user_repository.count({"role": query.role})
            
            serialized_users = [_serialize_user(user) for user in users]
            
            return QueryResult(
                data=serialized_users,
                total_count=total_count,
                page=query.skip // query.limit + 1,
                page_size=query.limit,
                has_next=(query.skip + query.limit) < total_count,
                has_previous=query.skip > 0
            )
        except ENABLEDRMException:
            return QueryResult(data=[])