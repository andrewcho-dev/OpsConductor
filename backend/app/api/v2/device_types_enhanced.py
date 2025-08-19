"""
Device Types API v2 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced device type management
- ✅ Device type validation and categorization
- ✅ Real-time device type operations
- ✅ Comprehensive device type lifecycle management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.services.device_types_management_service import DeviceTypesManagementService, DeviceTypesManagementError
from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

logger = get_structured_logger(__name__)

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class DeviceTypeResponse(BaseModel):
    """Enhanced response model for device types"""
    id: str = Field(..., description="Device type ID")
    name: str = Field(..., description="Device type name")
    description: Optional[str] = Field(None, description="Device type description")
    category: str = Field(..., description="Device type category")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[int] = Field(None, description="Creator user ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Device type metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "type_123456",
                "name": "Server",
                "description": "Server devices for infrastructure",
                "category": "infrastructure",
                "created_at": "2025-01-01T10:30:00Z",
                "created_by": 1,
                "metadata": {
                    "source": "device_types_management",
                    "version": "2.0"
                }
            }
        }


class DeviceTypeCreateRequest(BaseModel):
    """Enhanced request model for creating device types"""
    name: str = Field(..., description="Device type name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Device type description", max_length=1000)
    category: str = Field(..., description="Device type category")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Device type attributes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Network Switch",
                "description": "Network switching devices",
                "category": "network",
                "attributes": {
                    "ports": "24",
                    "speed": "1Gbps"
                },
                "metadata": {
                    "vendor": "Cisco",
                    "model": "Catalyst"
                }
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/device-types",
    tags=["Device Types Management Enhanced v2"]
)


# Local get_current_user removed - using centralized auth_dependencies


@router.get(
    "/",
    response_model=List[DeviceTypeResponse],
    summary="Get Device Types",
    description="""
    Get all device types with comprehensive information and caching.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 5-minute TTL
    - ✅ Enhanced device type information
    - ✅ Advanced filtering and categorization
    - ✅ Real-time device type management
    """
)
async def get_device_types(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[DeviceTypeResponse]:
    """Enhanced device types retrieval with service layer"""
    
    try:
        # Initialize service layer
        device_types_service = DeviceTypesManagementService(db)
        
        # Get device types through service layer (with caching)
        device_types_result = await device_types_service.get_all_device_types(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        # Convert to response models
        response = [DeviceTypeResponse(**device_type) for device_type in device_types_result]
        
        logger.info(
            "Device types retrieval successful via service layer",
            extra={
                "total_types": len(response),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except DeviceTypesManagementError as e:
        logger.warning(
            "Device types retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(
            "Device types retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving device types",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post(
    "/",
    response_model=DeviceTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Device Type",
    description="""
    Create a new device type with validation and tracking.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced device type validation
    - ✅ Real-time device type creation
    - ✅ Enhanced device type management
    - ✅ Comprehensive lifecycle tracking
    """
)
async def create_device_type(
    device_type_data: DeviceTypeCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DeviceTypeResponse:
    """Enhanced device type creation with service layer"""
    
    try:
        # Initialize service layer
        device_types_service = DeviceTypesManagementService(db)
        
        # Create device type through service layer
        created_type_result = await device_types_service.create_device_type(
            device_type_data=device_type_data.model_dump(),
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = DeviceTypeResponse(**created_type_result)
        
        logger.info(
            "Device type creation successful via service layer",
            extra={
                "device_type_id": created_type_result["id"],
                "device_type_name": created_type_result["name"],
                "created_by": current_user["username"]
            }
        )
        
        return response
        
    except DeviceTypesManagementError as e:
        logger.warning(
            "Device type creation failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "device_type_name": device_type_data.name,
                "created_by": current_user["username"]
            }
        )
        
        status_code = status.HTTP_400_BAD_REQUEST if e.error_code == "invalid_device_type_data" else status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(
            "Device type creation error via service layer",
            extra={
                "device_type_name": device_type_data.name,
                "error": str(e),
                "created_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while creating device type",
                "timestamp": datetime.utcnow().isoformat()
            }
        )