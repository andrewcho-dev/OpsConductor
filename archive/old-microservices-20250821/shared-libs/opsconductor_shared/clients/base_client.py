"""
Base HTTP client for inter-service communication
"""

import httpx
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from uuid import UUID

from opsconductor_shared.models.base import ServiceResponse, ServiceType

logger = logging.getLogger(__name__)


class BaseServiceClient:
    """Base client for inter-service HTTP communication"""
    
    def __init__(
        self,
        service_name: ServiceType,
        base_url: str,
        timeout: float = 30.0,
        auth_token: Optional[str] = None
    ):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.auth_token = auth_token
        
        # Create HTTP client
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"OpsConductor-Client/{service_name.value}"
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[UUID] = None
    ) -> ServiceResponse:
        """Make GET request to service"""
        return await self._request("GET", endpoint, params=params, correlation_id=correlation_id)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[UUID] = None
    ) -> ServiceResponse:
        """Make POST request to service"""
        return await self._request("POST", endpoint, json=data, correlation_id=correlation_id)
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[UUID] = None
    ) -> ServiceResponse:
        """Make PUT request to service"""
        return await self._request("PUT", endpoint, json=data, correlation_id=correlation_id)
    
    async def delete(
        self,
        endpoint: str,
        correlation_id: Optional[UUID] = None
    ) -> ServiceResponse:
        """Make DELETE request to service"""
        return await self._request("DELETE", endpoint, correlation_id=correlation_id)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        correlation_id: Optional[UUID] = None,
        **kwargs
    ) -> ServiceResponse:
        """Make HTTP request with error handling"""
        try:
            # Add correlation ID to headers
            headers = {}
            if correlation_id:
                headers["X-Correlation-ID"] = str(correlation_id)
            
            # Make request
            response = await self.client.request(
                method=method,
                url=endpoint,
                headers=headers,
                **kwargs
            )
            
            # Parse response
            if response.status_code < 400:
                try:
                    data = response.json()
                    return ServiceResponse(
                        success=True,
                        data=data,
                        service=self.service_name,
                        timestamp=datetime.utcnow()
                    )
                except Exception:
                    return ServiceResponse(
                        success=True,
                        message="Request successful",
                        service=self.service_name,
                        timestamp=datetime.utcnow()
                    )
            else:
                # Handle error response
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", f"HTTP {response.status_code}")
                except Exception:
                    error_message = f"HTTP {response.status_code}: {response.text}"
                
                return ServiceResponse(
                    success=False,
                    message=error_message,
                    errors=[error_message],
                    service=self.service_name,
                    timestamp=datetime.utcnow()
                )
                
        except httpx.TimeoutException:
            error_msg = f"Request to {self.service_name.value} timed out"
            logger.error(error_msg)
            return ServiceResponse(
                success=False,
                message=error_msg,
                errors=[error_msg],
                service=self.service_name,
                timestamp=datetime.utcnow()
            )
        except httpx.RequestError as e:
            error_msg = f"Request to {self.service_name.value} failed: {str(e)}"
            logger.error(error_msg)
            return ServiceResponse(
                success=False,
                message=error_msg,
                errors=[error_msg],
                service=self.service_name,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            error_msg = f"Unexpected error calling {self.service_name.value}: {str(e)}"
            logger.error(error_msg)
            return ServiceResponse(
                success=False,
                message=error_msg,
                errors=[error_msg],
                service=self.service_name,
                timestamp=datetime.utcnow()
            )
    
    async def health_check(self) -> ServiceResponse:
        """Check service health"""
        return await self.get("/health")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()