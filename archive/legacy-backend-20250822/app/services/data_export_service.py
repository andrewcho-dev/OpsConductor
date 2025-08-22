"""
Data Export Service
Handles data export operations with audit logging.
"""
import json
import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.audit_utils import log_audit_event_sync
from app.domains.audit.services.audit_service import AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

class DataExportService:
    """Service for data export operations with audit logging."""
    
    def __init__(self, db: Session):
        """
        Initialize the data export service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def export_data_to_json(
        self, 
        data: List[Dict[str, Any]], 
        export_type: str, 
        user_id: int,
        file_path: Optional[str] = None
    ) -> str:
        """
        Export data to JSON format with audit logging.
        
        Args:
            data: Data to export
            export_type: Type of data being exported (e.g., "targets", "users", "jobs")
            user_id: ID of the user performing the export
            file_path: Optional file path to save the exported data
            
        Returns:
            str: Path to the exported file or JSON string
        """
        try:
            # Create export directory if it doesn't exist
            export_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate timestamp for filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Use provided file path or generate one
            if not file_path:
                file_path = os.path.join(export_dir, f"{export_type}_export_{timestamp}.json")
            
            # Export data to JSON file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Log audit event
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.DATA_EXPORT,
                user_id=user_id,
                resource_type=export_type,
                resource_id="export",
                action="export_json",
                details={
                    "file_path": file_path,
                    "record_count": len(data),
                    "timestamp": timestamp,
                    "format": "json"
                },
                severity=AuditSeverity.MEDIUM
            )
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export data to JSON: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export data: {str(e)}"
            )
    
    def export_data_to_csv(
        self, 
        data: List[Dict[str, Any]], 
        export_type: str, 
        user_id: int,
        file_path: Optional[str] = None
    ) -> str:
        """
        Export data to CSV format with audit logging.
        
        Args:
            data: Data to export
            export_type: Type of data being exported (e.g., "targets", "users", "jobs")
            user_id: ID of the user performing the export
            file_path: Optional file path to save the exported data
            
        Returns:
            str: Path to the exported file
        """
        try:
            # Create export directory if it doesn't exist
            export_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate timestamp for filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Use provided file path or generate one
            if not file_path:
                file_path = os.path.join(export_dir, f"{export_type}_export_{timestamp}.csv")
            
            # Get field names from the first item
            if not data:
                raise ValueError("No data to export")
                
            fieldnames = data[0].keys()
            
            # Export data to CSV file
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in data:
                    # Convert any non-string values to strings
                    row = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                           for k, v in item.items()}
                    writer.writerow(row)
            
            # Log audit event
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.DATA_EXPORT,
                user_id=user_id,
                resource_type=export_type,
                resource_id="export",
                action="export_csv",
                details={
                    "file_path": file_path,
                    "record_count": len(data),
                    "timestamp": timestamp,
                    "format": "csv"
                },
                severity=AuditSeverity.MEDIUM
            )
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export data to CSV: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export data: {str(e)}"
            )
    
    def import_data_from_json(
        self, 
        file_path: str, 
        import_type: str, 
        user_id: int,
        validate_func: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Import data from JSON file with audit logging.
        
        Args:
            file_path: Path to the JSON file
            import_type: Type of data being imported (e.g., "targets", "users", "jobs")
            user_id: ID of the user performing the import
            validate_func: Optional function to validate the imported data
            
        Returns:
            List[Dict[str, Any]]: Imported data
        """
        try:
            # Read data from JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate data if validation function is provided
            if validate_func:
                data = validate_func(data)
            
            # Log audit event
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.DATA_IMPORT,
                user_id=user_id,
                resource_type=import_type,
                resource_id="import",
                action="import_json",
                details={
                    "file_path": file_path,
                    "record_count": len(data),
                    "timestamp": datetime.utcnow().isoformat(),
                    "format": "json"
                },
                severity=AuditSeverity.HIGH
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to import data from JSON: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import data: {str(e)}"
            )
    
    def import_data_from_csv(
        self, 
        file_path: str, 
        import_type: str, 
        user_id: int,
        validate_func: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Import data from CSV file with audit logging.
        
        Args:
            file_path: Path to the CSV file
            import_type: Type of data being imported (e.g., "targets", "users", "jobs")
            user_id: ID of the user performing the import
            validate_func: Optional function to validate the imported data
            
        Returns:
            List[Dict[str, Any]]: Imported data
        """
        try:
            # Read data from CSV file
            data = []
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            
            # Validate data if validation function is provided
            if validate_func:
                data = validate_func(data)
            
            # Log audit event
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.DATA_IMPORT,
                user_id=user_id,
                resource_type=import_type,
                resource_id="import",
                action="import_csv",
                details={
                    "file_path": file_path,
                    "record_count": len(data),
                    "timestamp": datetime.utcnow().isoformat(),
                    "format": "csv"
                },
                severity=AuditSeverity.HIGH
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to import data from CSV: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import data: {str(e)}"
            )
    
    def bulk_export(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        user_id: int,
        file_path: Optional[str] = None
    ) -> str:
        """
        Perform a bulk export of multiple data types with audit logging.
        
        Args:
            data: Dictionary of data types and their data
            user_id: ID of the user performing the export
            file_path: Optional file path to save the exported data
            
        Returns:
            str: Path to the exported file
        """
        try:
            # Create export directory if it doesn't exist
            export_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate timestamp for filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Use provided file path or generate one
            if not file_path:
                file_path = os.path.join(export_dir, f"bulk_export_{timestamp}.json")
            
            # Export data to JSON file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Calculate total record count
            total_records = sum(len(items) for items in data.values())
            
            # Log audit event
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.BULK_EXPORT,
                user_id=user_id,
                resource_type="bulk",
                resource_id="export",
                action="bulk_export",
                details={
                    "file_path": file_path,
                    "data_types": list(data.keys()),
                    "record_counts": {k: len(v) for k, v in data.items()},
                    "total_records": total_records,
                    "timestamp": timestamp,
                    "format": "json"
                },
                severity=AuditSeverity.HIGH
            )
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to perform bulk export: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to perform bulk export: {str(e)}"
            )
    
    def bulk_import(
        self, 
        file_path: str, 
        user_id: int,
        validate_funcs: Optional[Dict[str, callable]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a bulk import of multiple data types with audit logging.
        
        Args:
            file_path: Path to the JSON file
            user_id: ID of the user performing the import
            validate_funcs: Optional dictionary of validation functions for each data type
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Imported data
        """
        try:
            # Read data from JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate data if validation functions are provided
            if validate_funcs:
                for data_type, validate_func in validate_funcs.items():
                    if data_type in data:
                        data[data_type] = validate_func(data[data_type])
            
            # Calculate total record count
            total_records = sum(len(items) for items in data.values())
            
            # Log audit event
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.BULK_IMPORT,
                user_id=user_id,
                resource_type="bulk",
                resource_id="import",
                action="bulk_import",
                details={
                    "file_path": file_path,
                    "data_types": list(data.keys()),
                    "record_counts": {k: len(v) for k, v in data.items()},
                    "total_records": total_records,
                    "timestamp": datetime.utcnow().isoformat(),
                    "format": "json"
                },
                severity=AuditSeverity.HIGH
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to perform bulk import: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to perform bulk import: {str(e)}"
            )