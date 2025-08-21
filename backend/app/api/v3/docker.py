"""
Docker Management API v3 - Proxy to Portainer API
Provides Docker container, volume, and network management through Portainer
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import httpx
import asyncio
from typing import Dict, Any, Optional
import logging
from app.core.auth_dependencies import get_current_user

router = APIRouter(prefix="/api/v3/docker")
logger = logging.getLogger(__name__)

PORTAINER_BASE_URL = "http://portainer:9000/api"
ENDPOINT_ID = None  # Will be dynamically discovered

class PortainerClient:
    def __init__(self):
        self.token = None
        self.authenticated = False
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def authenticate(self):
        """Authenticate with Portainer API"""
        try:
            # Check if Portainer is initialized
            status_response = await self.client.get(f"{PORTAINER_BASE_URL}/status")
            status_data = status_response.json()
            
            if not status_data.get("UserCount", 0):
                # Initialize admin user if not exists
                await self.initialize_admin()
            
            # Authenticate
            auth_response = await self.client.post(f"{PORTAINER_BASE_URL}/auth", json={
                "Username": "admin",
                "Password": "opsconductor123"
            })
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                self.token = auth_data.get("jwt")
                self.authenticated = True
                
                # Set default headers
                self.client.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                return True
            else:
                logger.error(f"Portainer authentication failed: {auth_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Portainer authentication error: {e}")
            return False
    
    async def initialize_admin(self):
        """Initialize Portainer admin user"""
        try:
            await self.client.post(f"{PORTAINER_BASE_URL}/users/admin/init", json={
                "Username": "admin",
                "Password": "opsconductor123"
            })
        except Exception as e:
            logger.error(f"Failed to initialize Portainer admin: {e}")
    
    async def ensure_authenticated(self):
        """Ensure we're authenticated with Portainer"""
        if not self.authenticated:
            await self.authenticate()
    
    async def ensure_endpoint_exists(self):
        """Ensure Docker endpoint exists and discover endpoint ID"""
        global ENDPOINT_ID
        
        try:
            # Get list of endpoints to discover available ones
            endpoints_response = await self.client.get(
                f"{PORTAINER_BASE_URL}/endpoints",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if endpoints_response.status_code == 200:
                endpoints = endpoints_response.json()
                if len(endpoints) > 0:
                    # Use the first available endpoint
                    ENDPOINT_ID = endpoints[0]["Id"]
                    logger.info(f"Discovered and using endpoint ID: {ENDPOINT_ID} (Name: {endpoints[0].get('Name', 'Unknown')})")
                    return True
                else:
                    logger.error("No Docker endpoints found in Portainer. Please configure a Docker endpoint in Portainer first.")
                    return False
            else:
                logger.error(f"Failed to get endpoints list: {endpoints_response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to discover Docker endpoint: {e}")
            return False
    
    async def make_request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated request to Portainer API"""
        await self.ensure_authenticated()
        
        # Ensure endpoint exists before making Docker API calls
        if "/endpoints/" in endpoint and "/docker/" in endpoint:
            endpoint_exists = await self.ensure_endpoint_exists()
            if not endpoint_exists:
                raise HTTPException(status_code=503, detail="Docker endpoint not available")
        
        url = f"{PORTAINER_BASE_URL}{endpoint}"
        
        try:
            response = await self.client.request(method, url, **kwargs)
            
            if response.status_code == 401:
                # Token expired, re-authenticate
                self.authenticated = False
                await self.authenticate()
                response = await self.client.request(method, url, **kwargs)
            
            return response
        except Exception as e:
            logger.error(f"Portainer API request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Docker API request failed: {str(e)}")

# Global Portainer client instance
portainer_client = PortainerClient()

@router.get("/system/info")
async def get_system_info(current_user: dict = Depends(get_current_user)):
    """Get Docker system information"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/info"
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch system info")

@router.get("/containers")
async def get_containers(all: bool = True, current_user: dict = Depends(get_current_user)):
    """Get all containers"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/containers/json",
        params={"all": str(all).lower()}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch containers")

@router.get("/containers/{container_id}/stats")
async def get_container_stats(container_id: str, current_user: dict = Depends(get_current_user)):
    """Get container statistics"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/containers/{container_id}/stats",
        params={"stream": "false"}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch container stats")

@router.get("/containers/{container_id}/logs")
async def get_container_logs(
    container_id: str, 
    tail: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get container logs"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/containers/{container_id}/logs",
        params={
            "stdout": "true",
            "stderr": "true",
            "tail": str(tail),
            "timestamps": "true"
        }
    )
    
    if response.status_code == 200:
        return {"logs": response.text}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch container logs")

@router.post("/containers/{container_id}/start")
async def start_container(container_id: str, current_user: dict = Depends(get_current_user)):
    """Start a container"""
    response = await portainer_client.make_request(
        "POST", f"/endpoints/{ENDPOINT_ID}/docker/containers/{container_id}/start"
    )
    
    if response.status_code == 204:
        return {"success": True, "message": "Container started successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to start container")

@router.post("/containers/{container_id}/stop")
async def stop_container(container_id: str, current_user: dict = Depends(get_current_user)):
    """Stop a container"""
    response = await portainer_client.make_request(
        "POST", f"/endpoints/{ENDPOINT_ID}/docker/containers/{container_id}/stop"
    )
    
    if response.status_code == 204:
        return {"success": True, "message": "Container stopped successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to stop container")

@router.post("/containers/{container_id}/restart")
async def restart_container(container_id: str, current_user: dict = Depends(get_current_user)):
    """Restart a container"""
    response = await portainer_client.make_request(
        "POST", f"/endpoints/{ENDPOINT_ID}/docker/containers/{container_id}/restart"
    )
    
    if response.status_code == 204:
        return {"success": True, "message": "Container restarted successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to restart container")

@router.delete("/containers/{container_id}")
async def remove_container(container_id: str, force: bool = True, current_user: dict = Depends(get_current_user)):
    """Remove a container"""
    response = await portainer_client.make_request(
        "DELETE", f"/endpoints/{ENDPOINT_ID}/docker/containers/{container_id}",
        params={"force": str(force).lower()}
    )
    
    if response.status_code == 204:
        return {"success": True, "message": "Container removed successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to remove container")

@router.get("/volumes")
async def get_volumes(current_user: dict = Depends(get_current_user)):
    """Get all volumes"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/volumes"
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("Volumes", [])
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch volumes")

@router.get("/networks")
async def get_networks(current_user: dict = Depends(get_current_user)):
    """Get all networks"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/networks"
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch networks")

@router.get("/images")
async def get_images(current_user: dict = Depends(get_current_user)):
    """Get all images"""
    response = await portainer_client.make_request(
        "GET", f"/endpoints/{ENDPOINT_ID}/docker/images/json"
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch images")

@router.get("/status")
async def get_docker_status(current_user: dict = Depends(get_current_user)):
    """Get Docker daemon status and connectivity"""
    try:
        # Test connectivity by getting system info
        response = await portainer_client.make_request(
            "GET", f"/endpoints/{ENDPOINT_ID}/docker/info"
        )
        
        if response.status_code == 200:
            return {
                "status": "connected",
                "portainer_authenticated": portainer_client.authenticated,
                "message": "Docker daemon is accessible"
            }
        else:
            return {
                "status": "error",
                "portainer_authenticated": portainer_client.authenticated,
                "message": f"Docker daemon returned status {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "error",
            "portainer_authenticated": portainer_client.authenticated,
            "message": f"Failed to connect to Docker daemon: {str(e)}"
        }