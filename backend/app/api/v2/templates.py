"""
Templates API v2 - Universal Template Management
Consolidates all template management into a unified API.

This replaces and consolidates:
- /api/discovery/templates/* (discovery.py) - Discovery templates
- /api/notifications/templates/* (notifications.py) - Notification templates
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/templates", tags=["Templates Management v2"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_utc_timestamp() -> str:
    """Get current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# UNIVERSAL TEMPLATE MANAGEMENT
# ============================================================================

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    template_type: Optional[str] = Query(None, description="Filter by type: discovery, notification, job, custom"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description")
):
    """Get all templates with filtering."""
    try:
        # This would integrate with your template services
        templates = await get_templates_from_services(db, template_type, category, search)
        
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")


@router.get("/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template by ID."""
    try:
        template = await get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve template")


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new template."""
    try:
        # Validate template type
        template_type = template_data.get("type")
        if template_type not in ["discovery", "notification", "job", "custom"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid template type. Must be: discovery, notification, job, or custom"
            )
        
        template = await create_template_by_type(db, template_data, current_user.id)
        
        # Log template creation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="template",
            resource_id=str(template["id"]),
            action="create_template",
            details={"template_name": template["name"], "template_type": template_type},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.put("/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: int,
    template_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing template."""
    try:
        template = await update_template_by_id(db, template_id, template_data, current_user.id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Log template update
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_UPDATED,
            user_id=current_user.id,
            resource_type="template",
            resource_id=str(template_id),
            action="update_template",
            details={"template_name": template["name"], "updated_fields": list(template_data.keys())},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update template")


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a template."""
    try:
        template = await get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        success = await delete_template_by_id(db, template_id, current_user.id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete template")
        
        # Log template deletion
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_DELETED,
            user_id=current_user.id,
            resource_type="template",
            resource_id=str(template_id),
            action="delete_template",
            details={"template_name": template["name"]},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete template")


# ============================================================================
# DISCOVERY TEMPLATES (Consolidates: /api/discovery/templates/*)
# ============================================================================

@router.get("/discovery", response_model=List[Dict[str, Any]])
async def get_discovery_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by discovery category")
):
    """Get all discovery templates."""
    try:
        templates = await get_templates_from_services(db, "discovery", category, None)
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get discovery templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery templates")


@router.post("/discovery", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_discovery_template(
    template_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new discovery template."""
    try:
        # Add discovery type
        template_data["type"] = "discovery"
        
        # Validate discovery-specific fields
        required_fields = ["name", "description", "discovery_method", "target_criteria"]
        for field in required_fields:
            if field not in template_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field for discovery template: {field}"
                )
        
        template = await create_template_by_type(db, template_data, current_user.id)
        
        # Log discovery template creation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="discovery_template",
            resource_id=str(template["id"]),
            action="create_discovery_template",
            details={
                "template_name": template["name"], 
                "discovery_method": template_data["discovery_method"]
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create discovery template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create discovery template")


# ============================================================================
# NOTIFICATION TEMPLATES (Consolidates: /api/notifications/templates/*)
# ============================================================================

@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notification_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    notification_type: Optional[str] = Query(None, description="Filter by notification type: email, sms, webhook")
):
    """Get all notification templates."""
    try:
        templates = await get_templates_from_services(db, "notification", notification_type, None)
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get notification templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notification templates")


@router.post("/notifications", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_notification_template(
    template_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification template."""
    try:
        # Add notification type
        template_data["type"] = "notification"
        
        # Validate notification-specific fields
        required_fields = ["name", "description", "notification_type", "subject", "body"]
        for field in required_fields:
            if field not in template_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field for notification template: {field}"
                )
        
        # Validate notification type
        valid_types = ["email", "sms", "webhook", "slack", "teams"]
        if template_data["notification_type"] not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification type. Must be one of: {', '.join(valid_types)}"
            )
        
        template = await create_template_by_type(db, template_data, current_user.id)
        
        # Log notification template creation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="notification_template",
            resource_id=str(template["id"]),
            action="create_notification_template",
            details={
                "template_name": template["name"], 
                "notification_type": template_data["notification_type"]
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create notification template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification template")


# ============================================================================
# JOB TEMPLATES
# ============================================================================

@router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_job_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    job_type: Optional[str] = Query(None, description="Filter by job type")
):
    """Get all job templates."""
    try:
        templates = await get_templates_from_services(db, "job", job_type, None)
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get job templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job templates")


@router.post("/jobs", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_job_template(
    template_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job template."""
    try:
        # Add job type
        template_data["type"] = "job"
        
        # Validate job-specific fields
        required_fields = ["name", "description", "job_type", "actions", "target_criteria"]
        for field in required_fields:
            if field not in template_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field for job template: {field}"
                )
        
        template = await create_template_by_type(db, template_data, current_user.id)
        
        # Log job template creation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="job_template",
            resource_id=str(template["id"]),
            action="create_job_template",
            details={
                "template_name": template["name"], 
                "job_type": template_data["job_type"]
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create job template")


# ============================================================================
# TEMPLATE OPERATIONS
# ============================================================================

@router.post("/{template_id}/clone", response_model=Dict[str, Any])
async def clone_template(
    template_id: int,
    clone_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clone an existing template."""
    try:
        original_template = await get_template_by_id(db, template_id)
        if not original_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create clone with new name
        cloned_template = original_template.copy()
        cloned_template.update(clone_data)
        cloned_template["name"] = clone_data.get("name", f"{original_template['name']} (Copy)")
        
        template = await create_template_by_type(db, cloned_template, current_user.id)
        
        # Log template cloning
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="template",
            resource_id=str(template["id"]),
            action="clone_template",
            details={
                "original_template_id": template_id,
                "cloned_template_name": template["name"]
            },
            severity=AuditSeverity.LOW,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clone template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clone template")


@router.post("/{template_id}/validate", response_model=Dict[str, Any])
async def validate_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a template configuration."""
    try:
        template = await get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        validation_result = await validate_template_by_type(template)
        
        return {
            "template_id": template_id,
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "timestamp": get_utc_timestamp()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate template")


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk/delete", response_model=Dict[str, Any])
async def bulk_delete_templates(
    template_ids: List[int],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple templates at once."""
    try:
        results = []
        for template_id in template_ids:
            try:
                success = await delete_template_by_id(db, template_id, current_user.id)
                results.append({"template_id": template_id, "status": "deleted" if success else "not_found"})
            except Exception as e:
                results.append({"template_id": template_id, "status": "error", "error": str(e)})
        
        # Log bulk deletion
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.BULK_OPERATION,
            user_id=current_user.id,
            resource_type="template",
            resource_id="bulk",
            action="bulk_delete_templates",
            details={"template_ids": template_ids, "results_count": len(results)},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "success": True,
            "results": results,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk delete templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete templates")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_templates_from_services(db: Session, template_type: Optional[str], 
                                     category: Optional[str], search: Optional[str]) -> List[Dict[str, Any]]:
    """Get templates from various services based on type."""
    try:
        # This would integrate with your actual template services
        # For now, return mock data structure
        templates = []
        
        # Mock template data - replace with actual service calls
        mock_templates = [
            {
                "id": 1,
                "name": "Network Discovery Template",
                "type": "discovery",
                "category": "network",
                "description": "Standard network discovery template",
                "created_at": get_utc_timestamp(),
                "updated_at": get_utc_timestamp()
            },
            {
                "id": 2,
                "name": "Email Alert Template",
                "type": "notification",
                "category": "email",
                "description": "Standard email notification template",
                "created_at": get_utc_timestamp(),
                "updated_at": get_utc_timestamp()
            }
        ]
        
        # Apply filters
        for template in mock_templates:
            if template_type and template["type"] != template_type:
                continue
            if category and template["category"] != category:
                continue
            if search and search.lower() not in template["name"].lower() and search.lower() not in template["description"].lower():
                continue
            templates.append(template)
        
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get templates from services: {str(e)}")
        return []


async def get_template_by_id(db: Session, template_id: int) -> Optional[Dict[str, Any]]:
    """Get template by ID from appropriate service."""
    try:
        # This would route to the appropriate service based on template type
        # For now, return mock data
        if template_id == 1:
            return {
                "id": 1,
                "name": "Network Discovery Template",
                "type": "discovery",
                "category": "network",
                "description": "Standard network discovery template",
                "discovery_method": "ping_sweep",
                "target_criteria": {"network_range": "192.168.1.0/24"},
                "created_at": get_utc_timestamp(),
                "updated_at": get_utc_timestamp()
            }
        return None
        
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {str(e)}")
        return None


async def create_template_by_type(db: Session, template_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Create template using appropriate service based on type."""
    try:
        # This would route to the appropriate service
        # For now, return mock created template
        template_data["id"] = 999  # Mock ID
        template_data["created_at"] = get_utc_timestamp()
        template_data["updated_at"] = get_utc_timestamp()
        template_data["created_by"] = user_id
        
        return template_data
        
    except Exception as e:
        logger.error(f"Failed to create template: {str(e)}")
        raise


async def update_template_by_id(db: Session, template_id: int, template_data: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
    """Update template using appropriate service."""
    try:
        # This would route to the appropriate service
        # For now, return mock updated template
        template = await get_template_by_id(db, template_id)
        if template:
            template.update(template_data)
            template["updated_at"] = get_utc_timestamp()
            template["updated_by"] = user_id
            return template
        return None
        
    except Exception as e:
        logger.error(f"Failed to update template {template_id}: {str(e)}")
        return None


async def delete_template_by_id(db: Session, template_id: int, user_id: int) -> bool:
    """Delete template using appropriate service."""
    try:
        # This would route to the appropriate service
        # For now, return success for existing templates
        template = await get_template_by_id(db, template_id)
        return template is not None
        
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {str(e)}")
        return False


async def validate_template_by_type(template: Dict[str, Any]) -> Dict[str, Any]:
    """Validate template based on its type."""
    try:
        template_type = template.get("type")
        errors = []
        warnings = []
        
        # Basic validation
        if not template.get("name"):
            errors.append("Template name is required")
        
        if not template.get("description"):
            warnings.append("Template description is recommended")
        
        # Type-specific validation
        if template_type == "discovery":
            if not template.get("discovery_method"):
                errors.append("Discovery method is required")
            if not template.get("target_criteria"):
                errors.append("Target criteria is required")
                
        elif template_type == "notification":
            if not template.get("notification_type"):
                errors.append("Notification type is required")
            if not template.get("subject"):
                errors.append("Subject is required")
            if not template.get("body"):
                errors.append("Body is required")
                
        elif template_type == "job":
            if not template.get("job_type"):
                errors.append("Job type is required")
            if not template.get("actions"):
                errors.append("Actions are required")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        logger.error(f"Failed to validate template: {str(e)}")
        return {"is_valid": False, "errors": ["Validation failed"], "warnings": []}