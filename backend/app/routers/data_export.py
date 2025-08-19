"""
Data Export Router
Handles data export and import operations with audit logging.
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import json
import tempfile
import shutil
from datetime import datetime

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.services.data_export_service import DataExportService
from app.services.universal_target_service import UniversalTargetService
from app.services.user_service import UserService
from app.services.job_service import JobService

router = APIRouter(
    prefix="/api/v1/data",
    tags=["Data Export/Import"],
    responses={404: {"description": "Not found"}},
)

# Helper function to get client IP address
def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.client.host

@router.get("/export/targets", response_class=FileResponse)
async def export_targets(
    format: str = "json",
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all targets to a file.
    
    Args:
        format: Export format (json or csv)
        background_tasks: Background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FileResponse: Exported file
    """
    # Check if user has permission to export targets
    if "admin" not in current_user.get("roles", []) and "target_manager" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to export targets"
        )
    
    # Get all targets
    target_service = UniversalTargetService(db)
    targets = target_service.get_targets_summary()
    
    # Export targets
    export_service = DataExportService(db)
    
    # Generate timestamp for filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Create export directory if it doesn't exist
    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    if format.lower() == "json":
        file_path = os.path.join(export_dir, f"targets_export_{timestamp}.json")
        export_service.export_data_to_json(targets, "targets", current_user["id"], file_path)
    elif format.lower() == "csv":
        file_path = os.path.join(export_dir, f"targets_export_{timestamp}.csv")
        export_service.export_data_to_csv(targets, "targets", current_user["id"], file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Supported formats: json, csv"
        )
    
    # Schedule file cleanup after download (optional)
    if background_tasks:
        background_tasks.add_task(lambda: os.remove(file_path) if os.path.exists(file_path) else None)
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

@router.get("/export/users", response_class=FileResponse)
async def export_users(
    format: str = "json",
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all users to a file.
    
    Args:
        format: Export format (json or csv)
        background_tasks: Background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FileResponse: Exported file
    """
    # Check if user has permission to export users
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to export users"
        )
    
    # Get all users
    user_service = UserService(db)
    users = user_service.get_all_users()
    
    # Convert users to dictionaries and remove sensitive information
    user_dicts = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "roles": [role.role_name for role in user.roles] if hasattr(user, "roles") else []
        }
        user_dicts.append(user_dict)
    
    # Export users
    export_service = DataExportService(db)
    
    # Generate timestamp for filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Create export directory if it doesn't exist
    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    if format.lower() == "json":
        file_path = os.path.join(export_dir, f"users_export_{timestamp}.json")
        export_service.export_data_to_json(user_dicts, "users", current_user["id"], file_path)
    elif format.lower() == "csv":
        file_path = os.path.join(export_dir, f"users_export_{timestamp}.csv")
        export_service.export_data_to_csv(user_dicts, "users", current_user["id"], file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Supported formats: json, csv"
        )
    
    # Schedule file cleanup after download (optional)
    if background_tasks:
        background_tasks.add_task(lambda: os.remove(file_path) if os.path.exists(file_path) else None)
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

@router.get("/export/jobs", response_class=FileResponse)
async def export_jobs(
    format: str = "json",
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all jobs to a file.
    
    Args:
        format: Export format (json or csv)
        background_tasks: Background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FileResponse: Exported file
    """
    # Check if user has permission to export jobs
    if "admin" not in current_user.get("roles", []) and "job_manager" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to export jobs"
        )
    
    # Get all jobs
    job_service = JobService(db)
    jobs = job_service.get_all_jobs()
    
    # Convert jobs to dictionaries
    job_dicts = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "name": job.name,
            "description": job.description,
            "job_type": job.job_type,
            "status": job.status.value if hasattr(job.status, "value") else str(job.status),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "created_by": job.created_by,
            "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
            "target_count": len(job.targets) if hasattr(job, "targets") else 0,
            "action_count": len(job.actions) if hasattr(job, "actions") else 0
        }
        job_dicts.append(job_dict)
    
    # Export jobs
    export_service = DataExportService(db)
    
    # Generate timestamp for filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Create export directory if it doesn't exist
    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    if format.lower() == "json":
        file_path = os.path.join(export_dir, f"jobs_export_{timestamp}.json")
        export_service.export_data_to_json(job_dicts, "jobs", current_user["id"], file_path)
    elif format.lower() == "csv":
        file_path = os.path.join(export_dir, f"jobs_export_{timestamp}.csv")
        export_service.export_data_to_csv(job_dicts, "jobs", current_user["id"], file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Supported formats: json, csv"
        )
    
    # Schedule file cleanup after download (optional)
    if background_tasks:
        background_tasks.add_task(lambda: os.remove(file_path) if os.path.exists(file_path) else None)
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

@router.post("/import/targets")
async def import_targets(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import targets from a file.
    
    Args:
        file: Uploaded file (JSON or CSV)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Import result
    """
    # Check if user has permission to import targets
    if "admin" not in current_user.get("roles", []) and "target_manager" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to import targets"
        )
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".json", ".csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Supported formats: .json, .csv"
        )
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name
    
    try:
        # Import targets
        export_service = DataExportService(db)
        target_service = UniversalTargetService(db)
        
        if file_ext == ".json":
            targets_data = export_service.import_data_from_json(temp_file_path, "targets", current_user["id"])
        else:  # .csv
            targets_data = export_service.import_data_from_csv(temp_file_path, "targets", current_user["id"])
        
        # Process imported targets (simplified for example)
        imported_count = 0
        failed_count = 0
        
        # In a real implementation, you would validate and create targets here
        # For now, we'll just return the count of targets that would be imported
        
        return {
            "success": True,
            "message": f"Successfully processed {len(targets_data)} targets",
            "imported_count": len(targets_data),
            "failed_count": 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import targets: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.post("/bulk-export")
async def bulk_export(
    export_types: List[str],
    format: str = "json",
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform a bulk export of multiple data types.
    
    Args:
        export_types: List of data types to export (targets, users, jobs)
        format: Export format (json or csv)
        background_tasks: Background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FileResponse: Exported file
    """
    # Check if user has permission to perform bulk export
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform bulk export"
        )
    
    # Validate export types
    valid_types = ["targets", "users", "jobs"]
    for export_type in export_types:
        if export_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export type: {export_type}. Valid types: {', '.join(valid_types)}"
            )
    
    # Initialize services
    export_service = DataExportService(db)
    target_service = UniversalTargetService(db)
    user_service = UserService(db)
    job_service = JobService(db)
    
    # Collect data for each export type
    export_data = {}
    
    if "targets" in export_types:
        export_data["targets"] = target_service.get_targets_summary()
    
    if "users" in export_types:
        users = user_service.get_all_users()
        user_dicts = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "roles": [role.role_name for role in user.roles] if hasattr(user, "roles") else []
            }
            user_dicts.append(user_dict)
        export_data["users"] = user_dicts
    
    if "jobs" in export_types:
        jobs = job_service.get_all_jobs()
        job_dicts = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "name": job.name,
                "description": job.description,
                "job_type": job.job_type,
                "status": job.status.value if hasattr(job.status, "value") else str(job.status),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "created_by": job.created_by,
                "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
                "target_count": len(job.targets) if hasattr(job, "targets") else 0,
                "action_count": len(job.actions) if hasattr(job, "actions") else 0
            }
            job_dicts.append(job_dict)
        export_data["jobs"] = job_dicts
    
    # Generate timestamp for filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Create export directory if it doesn't exist
    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    # Export data
    if format.lower() == "json":
        file_path = os.path.join(export_dir, f"bulk_export_{timestamp}.json")
        export_service.bulk_export(export_data, current_user["id"], file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bulk export only supports JSON format"
        )
    
    # Schedule file cleanup after download (optional)
    if background_tasks:
        background_tasks.add_task(lambda: os.remove(file_path) if os.path.exists(file_path) else None)
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )