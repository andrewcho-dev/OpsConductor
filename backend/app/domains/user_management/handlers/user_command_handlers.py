"""
User Management Command Handlers
"""
from app.shared.infrastructure.cqrs import CommandHandler, CommandResult, command_handler
from app.domains.user_management.commands.user_commands import (
    CreateUserCommand, UpdateUserCommand, ChangePasswordCommand,
    DeactivateUserCommand, ActivateUserCommand, AuthenticateUserCommand
)
from app.domains.user_management.services.user_domain_service import UserDomainService
from app.shared.infrastructure.container import inject
from app.shared.exceptions.base import ENABLEDRMException


@command_handler(CreateUserCommand)
class CreateUserCommandHandler(CommandHandler[CreateUserCommand, CommandResult]):
    """Handler for creating users."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, command: CreateUserCommand) -> CommandResult:
        """Handle user creation command."""
        try:
            user = await user_service.create_user(
                username=command.username,
                email=command.email,
                password=command.password,
                role=command.role
            )
            
            return CommandResult(
                success=True,
                data={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                message="User created successfully"
            )
        except ENABLEDRMException as e:
            return CommandResult(
                success=False,
                message=str(e),
                errors={"error_code": e.error_code, "details": e.details}
            )


@command_handler(UpdateUserCommand)
class UpdateUserCommandHandler(CommandHandler[UpdateUserCommand, CommandResult]):
    """Handler for updating users."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, command: UpdateUserCommand) -> CommandResult:
        """Handle user update command."""
        try:
            user = await user_service.update_user(
                user_id=command.user_id,
                update_data=command.update_data
            )
            
            return CommandResult(
                success=True,
                data={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                },
                message="User updated successfully"
            )
        except ENABLEDRMException as e:
            return CommandResult(
                success=False,
                message=str(e),
                errors={"error_code": e.error_code, "details": e.details}
            )


@command_handler(ChangePasswordCommand)
class ChangePasswordCommandHandler(CommandHandler[ChangePasswordCommand, CommandResult]):
    """Handler for changing user passwords."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, command: ChangePasswordCommand) -> CommandResult:
        """Handle password change command."""
        try:
            user = await user_service.change_password(
                user_id=command.user_id,
                current_password=command.current_password,
                new_password=command.new_password
            )
            
            return CommandResult(
                success=True,
                data={"user_id": user.id},
                message="Password changed successfully"
            )
        except ENABLEDRMException as e:
            return CommandResult(
                success=False,
                message=str(e),
                errors={"error_code": e.error_code, "details": e.details}
            )


@command_handler(DeactivateUserCommand)
class DeactivateUserCommandHandler(CommandHandler[DeactivateUserCommand, CommandResult]):
    """Handler for deactivating users."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, command: DeactivateUserCommand) -> CommandResult:
        """Handle user deactivation command."""
        try:
            user = await user_service.deactivate_user(command.user_id)
            
            return CommandResult(
                success=True,
                data={"user_id": user.id, "is_active": user.is_active},
                message="User deactivated successfully"
            )
        except ENABLEDRMException as e:
            return CommandResult(
                success=False,
                message=str(e),
                errors={"error_code": e.error_code, "details": e.details}
            )


@command_handler(ActivateUserCommand)
class ActivateUserCommandHandler(CommandHandler[ActivateUserCommand, CommandResult]):
    """Handler for activating users."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, command: ActivateUserCommand) -> CommandResult:
        """Handle user activation command."""
        try:
            user = await user_service.activate_user(command.user_id)
            
            return CommandResult(
                success=True,
                data={"user_id": user.id, "is_active": user.is_active},
                message="User activated successfully"
            )
        except ENABLEDRMException as e:
            return CommandResult(
                success=False,
                message=str(e),
                errors={"error_code": e.error_code, "details": e.details}
            )


@command_handler(AuthenticateUserCommand)
class AuthenticateUserCommandHandler(CommandHandler[AuthenticateUserCommand, CommandResult]):
    """Handler for user authentication."""
    
    @inject(UserDomainService)
    async def handle(self, user_service: UserDomainService, command: AuthenticateUserCommand) -> CommandResult:
        """Handle user authentication command."""
        try:
            user = await user_service.authenticate_user(
                username=command.username,
                password=command.password
            )
            
            if user:
                return CommandResult(
                    success=True,
                    data={
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "last_login": user.last_login.isoformat() if user.last_login else None
                    },
                    message="Authentication successful"
                )
            else:
                return CommandResult(
                    success=False,
                    message="Invalid credentials"
                )
        except ENABLEDRMException as e:
            return CommandResult(
                success=False,
                message=str(e),
                errors={"error_code": e.error_code, "details": e.details}
            )