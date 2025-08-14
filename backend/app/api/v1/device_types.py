"""
Device Type Management API
Exposes the centralized device type system with discovery capabilities
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Set
from app.core.device_types import (
    device_registry, 
    DeviceCategory, 
    get_valid_device_types,
    get_communication_methods_for_device_type,
    suggest_device_type_from_discovery
)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.security import verify_token
from app.models.user_models import User

# Security
security = HTTPBearer()

# Dependency to verify JWT token
async def get_current_user(credentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

router = APIRouter(prefix="/api/v1/device-types", tags=["Device Types"])


@router.get("/", response_model=List[Dict])
async def get_all_device_types(current_user: User = Depends(get_current_user)):
    """
    Get all device types with their communication methods and discovery hints
    """
    device_types = device_registry.get_all_device_types()
    
    result = []
    for device_type in device_types:
        result.append({
            "value": device_type.value,
            "label": device_type.label,
            "category": device_type.category.value,
            "description": device_type.description,
            "communication_methods": list(device_type.communication_methods),
            "discovery_ports": device_type.discovery_ports,
            "discovery_services": device_type.discovery_services,
            "discovery_keywords": device_type.discovery_keywords
        })
    
    return result


@router.get("/categories", response_model=List[Dict])
async def get_device_categories(current_user: User = Depends(get_current_user)):
    """
    Get all device categories
    """
    categories = []
    for category in DeviceCategory:
        # Get device types for this category
        device_types = device_registry.get_device_types_by_category(category)
        
        categories.append({
            "value": category.value,
            "label": category.value.replace("_", " ").title(),
            "device_count": len(device_types),
            "device_types": [dt.value for dt in device_types]
        })
    
    return categories


@router.get("/by-category/{category}", response_model=List[Dict])
async def get_device_types_by_category(
    category: str, 
    current_user: User = Depends(get_current_user)
):
    """
    Get device types by category
    """
    try:
        device_category = DeviceCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    device_types = device_registry.get_device_types_by_category(device_category)
    
    result = []
    for device_type in device_types:
        result.append({
            "value": device_type.value,
            "label": device_type.label,
            "description": device_type.description,
            "communication_methods": list(device_type.communication_methods)
        })
    
    return result


@router.get("/{device_type}/communication-methods", response_model=List[str])
async def get_communication_methods_for_device(
    device_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get communication methods for a specific device type
    """
    methods = device_registry.get_communication_methods_for_device(device_type)
    if not methods:
        raise HTTPException(status_code=404, detail=f"Device type not found: {device_type}")
    
    return list(methods)


@router.get("/communication-methods/{method}/device-types", response_model=List[Dict])
async def get_device_types_for_method(
    method: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get device types that support a specific communication method
    """
    device_types = device_registry.get_device_types_for_method(method)
    
    result = []
    for device_type in device_types:
        result.append({
            "value": device_type.value,
            "label": device_type.label,
            "category": device_type.category.value,
            "description": device_type.description
        })
    
    return result


@router.get("/{device_type}/discovery-hints", response_model=Dict)
async def get_discovery_hints(
    device_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get discovery hints for a device type (ports, services, keywords)
    """
    hints = device_registry.get_discovery_hints(device_type)
    if not hints:
        raise HTTPException(status_code=404, detail=f"Device type not found: {device_type}")
    
    return hints


@router.post("/suggest", response_model=List[Dict])
async def suggest_device_types(
    ports: List[int],
    services: List[str] = [],
    banner: str = "",
    current_user: User = Depends(get_current_user)
):
    """
    Suggest device types based on discovered information
    """
    suggestions = device_registry.suggest_device_type(ports, services, banner)
    
    result = []
    for device_type_value in suggestions:
        device_type = device_registry.get_device_type(device_type_value)
        if device_type:
            result.append({
                "value": device_type.value,
                "label": device_type.label,
                "category": device_type.category.value,
                "description": device_type.description,
                "communication_methods": list(device_type.communication_methods)
            })
    
    return result


@router.get("/valid-types", response_model=List[str])
async def get_valid_device_types_endpoint(current_user: User = Depends(get_current_user)):
    """
    Get list of valid device type values (for backward compatibility)
    """
    from app.core.device_types import get_valid_device_types
    return get_valid_device_types()


@router.get("/communication-methods", response_model=List[str])
async def get_all_communication_methods(current_user: User = Depends(get_current_user)):
    """
    Get all available communication methods
    """
    all_methods = set()
    for device_type in device_registry.get_all_device_types():
        all_methods.update(device_type.communication_methods)
    
    return sorted(list(all_methods))
