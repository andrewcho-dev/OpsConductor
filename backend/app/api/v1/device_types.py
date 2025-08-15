"""
Device Type Management API v1
Exposes the centralized device type system with discovery capabilities

IMPROVEMENT STATUS: Phase 1 - Code Quality Fixes Applied
- ✅ Fixed duplicate imports
- ✅ Using centralized authentication
- ✅ Added proper response models
- ✅ Improved error handling
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.core.device_types import (
    device_registry, 
    DeviceCategory, 
    get_valid_device_types,
    get_communication_methods_for_device_type,
    suggest_device_type_from_discovery
)
from app.models.user_models import User

# Import centralized authentication from main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import get_current_user

# Response Models for better API documentation and type safety
class DeviceTypeResponse(BaseModel):
    """Response model for device type information"""
    value: str = Field(..., description="Device type identifier")
    label: str = Field(..., description="Human-readable label")
    category: str = Field(..., description="Device category")
    description: str = Field(..., description="Device description")
    communication_methods: List[str] = Field(..., description="Supported communication methods")
    discovery_ports: List[int] = Field(default=[], description="Common ports for discovery")
    discovery_services: List[str] = Field(default=[], description="Common services for discovery")
    discovery_keywords: List[str] = Field(default=[], description="Keywords for identification")

class DeviceCategoryResponse(BaseModel):
    """Response model for device category information"""
    value: str = Field(..., description="Category identifier")
    label: str = Field(..., description="Human-readable label")
    device_count: int = Field(..., description="Number of device types in category")
    device_types: List[str] = Field(..., description="Device type identifiers in category")

class DeviceTypeBasicResponse(BaseModel):
    """Basic device type response for simplified endpoints"""
    value: str = Field(..., description="Device type identifier")
    label: str = Field(..., description="Human-readable label")
    category: str = Field(..., description="Device category")
    description: str = Field(..., description="Device description")
    communication_methods: List[str] = Field(..., description="Supported communication methods")

class DiscoveryHintsResponse(BaseModel):
    """Response model for discovery hints"""
    ports: List[int] = Field(default=[], description="Common ports")
    services: List[str] = Field(default=[], description="Common services")
    keywords: List[str] = Field(default=[], description="Identification keywords")

class DeviceTypeSuggestionRequest(BaseModel):
    """Request model for device type suggestions"""
    ports: List[int] = Field(..., description="Discovered ports")
    services: List[str] = Field(default=[], description="Discovered services")
    banner: str = Field(default="", description="Service banner or response")

router = APIRouter(prefix="/api/v1/device-types", tags=["Device Types v1"])


@router.get("/", response_model=List[DeviceTypeResponse])
async def get_all_device_types(current_user: User = Depends(get_current_user)):
    """
    Get all device types with their communication methods and discovery hints.
    
    Returns comprehensive information about all available device types including
    discovery hints for network scanning and device identification.
    """
    try:
        device_types = device_registry.get_all_device_types()
        
        result = []
        for device_type in device_types:
            result.append(DeviceTypeResponse(
                value=device_type.value,
                label=device_type.label,
                category=device_type.category.value,
                description=device_type.description,
                communication_methods=list(device_type.communication_methods),
                discovery_ports=device_type.discovery_ports or [],
                discovery_services=device_type.discovery_services or [],
                discovery_keywords=device_type.discovery_keywords or []
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device types: {str(e)}"
        )


@router.get("/categories", response_model=List[DeviceCategoryResponse])
async def get_device_categories(current_user: User = Depends(get_current_user)):
    """
    Get all device categories with device counts and type lists.
    
    Returns information about all device categories including the number
    of device types in each category and their identifiers.
    """
    try:
        categories = []
        for category in DeviceCategory:
            # Get device types for this category
            device_types = device_registry.get_device_types_by_category(category)
            
            categories.append(DeviceCategoryResponse(
                value=category.value,
                label=category.value.replace("_", " ").title(),
                device_count=len(device_types),
                device_types=[dt.value for dt in device_types]
            ))
        
        return categories
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device categories: {str(e)}"
        )


@router.get("/by-category/{category}", response_model=List[DeviceTypeBasicResponse])
async def get_device_types_by_category(
    category: str, 
    current_user: User = Depends(get_current_user)
):
    """
    Get device types by category.
    
    Returns all device types that belong to the specified category.
    Category names are case-sensitive and should match the enum values.
    """
    try:
        # Validate category parameter
        try:
            device_category = DeviceCategory(category)
        except ValueError:
            available_categories = [cat.value for cat in DeviceCategory]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid category '{category}'. Available categories: {available_categories}"
            )
        
        device_types = device_registry.get_device_types_by_category(device_category)
        
        result = []
        for device_type in device_types:
            result.append(DeviceTypeBasicResponse(
                value=device_type.value,
                label=device_type.label,
                category=device_type.category.value,
                description=device_type.description,
                communication_methods=list(device_type.communication_methods)
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device types for category '{category}': {str(e)}"
        )


@router.get("/{device_type}/communication-methods", response_model=List[str])
async def get_communication_methods_for_device(
    device_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get communication methods for a specific device type.
    
    Returns the list of communication methods supported by the specified device type.
    """
    try:
        methods = device_registry.get_communication_methods_for_device(device_type)
        if not methods:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Device type '{device_type}' not found"
            )
        
        return list(methods)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve communication methods for '{device_type}': {str(e)}"
        )


@router.get("/communication-methods/{method}/device-types", response_model=List[DeviceTypeBasicResponse])
async def get_device_types_for_method(
    method: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get device types that support a specific communication method.
    
    Returns all device types that support the specified communication method.
    """
    try:
        device_types = device_registry.get_device_types_for_method(method)
        
        result = []
        for device_type in device_types:
            result.append(DeviceTypeBasicResponse(
                value=device_type.value,
                label=device_type.label,
                category=device_type.category.value,
                description=device_type.description,
                communication_methods=list(device_type.communication_methods)
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device types for method '{method}': {str(e)}"
        )


@router.get("/{device_type}/discovery-hints", response_model=DiscoveryHintsResponse)
async def get_discovery_hints(
    device_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get discovery hints for a device type (ports, services, keywords).
    
    Returns discovery information that can be used for network scanning
    and device identification.
    """
    try:
        hints = device_registry.get_discovery_hints(device_type)
        if not hints:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Device type '{device_type}' not found"
            )
        
        return DiscoveryHintsResponse(
            ports=hints.get('ports', []),
            services=hints.get('services', []),
            keywords=hints.get('keywords', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve discovery hints for '{device_type}': {str(e)}"
        )


@router.post("/suggest", response_model=List[DeviceTypeBasicResponse])
async def suggest_device_types(
    request: DeviceTypeSuggestionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Suggest device types based on discovered information.
    
    Analyzes discovered ports, services, and banners to suggest
    the most likely device types.
    """
    try:
        suggestions = device_registry.suggest_device_type(
            request.ports, 
            request.services, 
            request.banner
        )
        
        result = []
        for device_type_value in suggestions:
            device_type = device_registry.get_device_type(device_type_value)
            if device_type:
                result.append(DeviceTypeBasicResponse(
                    value=device_type.value,
                    label=device_type.label,
                    category=device_type.category.value,
                    description=device_type.description,
                    communication_methods=list(device_type.communication_methods)
                ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest device types: {str(e)}"
        )


@router.get("/valid-types", response_model=List[str])
async def get_valid_device_types_endpoint(current_user: User = Depends(get_current_user)):
    """
    Get list of valid device type values (for backward compatibility).
    
    Returns a simple list of device type identifiers for legacy compatibility.
    """
    try:
        from app.core.device_types import get_valid_device_types
        return get_valid_device_types()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve valid device types: {str(e)}"
        )


@router.get("/communication-methods", response_model=List[str])
async def get_all_communication_methods(current_user: User = Depends(get_current_user)):
    """
    Get all available communication methods.
    
    Returns a sorted list of all communication methods supported
    by any device type in the registry.
    """
    try:
        all_methods = set()
        for device_type in device_registry.get_all_device_types():
            all_methods.update(device_type.communication_methods)
        
        return sorted(list(all_methods))
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve communication methods: {str(e)}"
        )
