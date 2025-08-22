"""
Target Domain Service - Contains business logic for target management.
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import asyncio
import ipaddress
import socket
import re

from app.shared.exceptions.base import ValidationException, ConflictError, NotFoundError
from app.domains.target_management.repositories.target_repository import TargetRepository
from app.models.universal_target_models import UniversalTarget
from app.shared.infrastructure.container import injectable
from app.shared.infrastructure.events import event_bus
from app.domains.target_management.events.target_events_simple import (
    TargetCreatedEvent, TargetUpdatedEvent, TargetDeletedEvent,
    TargetConnectionTestEvent, BulkTargetOperationEvent
)


@injectable()
class TargetDomainService:
    """Domain service for target management business logic."""
    
    def __init__(self, target_repository: TargetRepository):
        self.target_repository = target_repository
    
    async def create_target(
        self,
        name: str,
        host: str,
        target_type: str,
        port: int,
        credentials: Dict[str, Any],
        created_by: int,
        description: str = "",
        tags: Optional[List[str]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> UniversalTarget:
        """Create a new target with validation."""
        # Validate input
        await self._validate_target_creation(name, host, target_type, port)
        
        # Check for conflicts
        existing_target = await self.target_repository.get_by_name(name)
        if existing_target:
            raise ConflictError(f"Target with name '{name}' already exists")
        
        existing_host = await self.target_repository.get_by_host(host)
        if existing_host and existing_host.port == port:
            raise ConflictError(f"Target with host '{host}:{port}' already exists")
        
        # Create target data
        target_data = {
            "name": name,
            "host": host,
            "port": port,
            "target_type": target_type,
            "description": description,
            "credentials": credentials,
            "tags": tags or [],
            "custom_config": custom_config or {},
            "status": "unknown",
            "is_active": True,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        target = await self.target_repository.create(target_data)
        
        # Publish domain event
        event = TargetCreatedEvent(
            target_id=target.id,
            target_name=target.name,
            target_type=target.target_type,
            host=target.host,
            port=target.port,
            created_by=created_by
        )
        await event_bus.publish(event)
        
        return target
    
    async def update_target(
        self,
        target_id: int,
        update_data: Dict[str, Any],
        updated_by: int
    ) -> UniversalTarget:
        """Update target with validation."""
        target = await self.target_repository.get_by_id_or_raise(target_id)
        
        # Validate updates
        if "name" in update_data and update_data["name"] != target.name:
            existing_target = await self.target_repository.get_by_name(update_data["name"])
            if existing_target and existing_target.id != target_id:
                raise ConflictError(f"Target with name '{update_data['name']}' already exists")
        
        if "host" in update_data or "port" in update_data:
            new_host = update_data.get("host", target.host)
            new_port = update_data.get("port", target.port)
            
            if new_host != target.host or new_port != target.port:
                existing_host = await self.target_repository.get_by_host(new_host)
                if existing_host and existing_host.port == new_port and existing_host.id != target_id:
                    raise ConflictError(f"Target with host '{new_host}:{new_port}' already exists")
        
        # Track changes for event
        changes = {k: v for k, v in update_data.items() if getattr(target, k, None) != v}
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated_target = await self.target_repository.update(target_id, update_data)
        
        # Publish domain event
        if changes:
            event = TargetUpdatedEvent(
                target_id=target.id,
                target_name=target.name,
                changes=changes,
                updated_by=updated_by
            )
            await event_bus.publish(event)
        
        return updated_target
    
    async def delete_target(self, target_id: int, deleted_by: int) -> bool:
        """Delete target."""
        target = await self.target_repository.get_by_id_or_raise(target_id)
        
        # Check if target is being used in any jobs
        # This would require checking job dependencies - simplified for now
        
        result = await self.target_repository.delete(target_id)
        
        if result:
            # Publish domain event
            event = TargetDeletedEvent(
                target_id=target.id,
                target_name=target.name,
                target_type=target.target_type,
                deleted_by=deleted_by
            )
            await event_bus.publish(event)
        
        return result
    
    async def test_target_connection(self, target_id: int, tested_by: int) -> Dict[str, Any]:
        """Test connection to target."""
        target = await self.target_repository.get_by_id_or_raise(target_id)
        
        test_result = await self._perform_connection_test(target)
        
        # Update target status based on test result
        new_status = "online" if test_result["success"] else "offline"
        await self.target_repository.update_target_status(
            target_id=target_id,
            status=new_status,
            last_check=datetime.now(timezone.utc)
        )
        
        # Publish domain event
        event = TargetConnectionTestEvent(
            target_id=target.id,
            target_name=target.name,
            test_result=test_result,
            tested_by=tested_by
        )
        await event_bus.publish(event)
        
        return test_result
    
    async def bulk_test_connections(self, target_ids: List[int], tested_by: int) -> Dict[str, Any]:
        """Test connections to multiple targets."""
        targets = await self.target_repository.get_targets_for_bulk_operation(target_ids)
        
        if len(targets) != len(target_ids):
            found_ids = {t.id for t in targets}
            missing_ids = set(target_ids) - found_ids
            raise NotFoundError(f"Targets not found: {missing_ids}")
        
        # Test connections concurrently
        test_tasks = [self._perform_connection_test(target) for target in targets]
        test_results = await asyncio.gather(*test_tasks, return_exceptions=True)
        
        # Process results
        results = {}
        status_updates = []
        
        for target, result in zip(targets, test_results):
            if isinstance(result, Exception):
                test_result = {
                    "success": False,
                    "error": str(result),
                    "response_time": None,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                test_result = result
            
            results[target.id] = test_result
            
            # Prepare status update
            new_status = "online" if test_result["success"] else "offline"
            status_updates.append(target.id)
            
            # Update individual target status
            await self.target_repository.update_target_status(
                target_id=target.id,
                status=new_status,
                last_check=datetime.now(timezone.utc)
            )
        
        # Publish bulk operation event
        event = BulkTargetOperationEvent(
            operation_type="connection_test",
            target_ids=target_ids,
            results=results,
            performed_by=tested_by
        )
        await event_bus.publish(event)
        
        return {
            "total_tested": len(targets),
            "successful": sum(1 for r in results.values() if r["success"]),
            "failed": sum(1 for r in results.values() if not r["success"]),
            "results": results
        }
    
    async def bulk_update_targets(
        self,
        target_ids: List[int],
        update_data: Dict[str, Any],
        updated_by: int
    ) -> Dict[str, Any]:
        """Bulk update multiple targets."""
        targets = await self.target_repository.get_targets_for_bulk_operation(target_ids)
        
        if len(targets) != len(target_ids):
            found_ids = {t.id for t in targets}
            missing_ids = set(target_ids) - found_ids
            raise NotFoundError(f"Targets not found: {missing_ids}")
        
        # Validate bulk update data
        self._validate_bulk_update_data(update_data)
        
        # Perform bulk update
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        updated_count = 0
        for target_id in target_ids:
            try:
                await self.target_repository.update(target_id, update_data)
                updated_count += 1
            except Exception as e:
                # Log error but continue with other targets
                print(f"Failed to update target {target_id}: {e}")
        
        # Publish bulk operation event
        event = BulkTargetOperationEvent(
            operation_type="bulk_update",
            target_ids=target_ids,
            results={"updated_count": updated_count, "update_data": update_data},
            performed_by=updated_by
        )
        await event_bus.publish(event)
        
        return {
            "total_targets": len(target_ids),
            "updated_count": updated_count,
            "failed_count": len(target_ids) - updated_count
        }
    
    async def get_targets_needing_health_check(self, minutes_since_last_check: int = 30) -> List[UniversalTarget]:
        """Get targets that need health check."""
        return await self.target_repository.get_targets_needing_health_check(minutes_since_last_check)
    
    async def perform_health_check(self, minutes_since_last_check: int = 30) -> Dict[str, Any]:
        """Perform health check on targets that need it."""
        return await self.perform_health_checks()
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on targets that need it."""
        targets = await self.get_targets_needing_health_check()
        
        if not targets:
            return {"message": "No targets need health check", "checked_count": 0}
        
        # Perform health checks
        target_ids = [t.id for t in targets]
        results = await self.bulk_test_connections(target_ids, tested_by=0)  # System user
        
        return {
            "message": f"Health check completed for {len(targets)} targets",
            "checked_count": len(targets),
            "results": results
        }
    
    async def search_targets(
        self,
        search_term: str = "",
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UniversalTarget]:
        """Search targets with filters."""
        return await self.target_repository.search_targets(search_term, filters, skip, limit)
    
    async def get_target_statistics(self) -> Dict[str, Any]:
        """Get comprehensive target statistics."""
        stats = await self.target_repository.get_target_statistics()
        
        # Add additional computed statistics
        stats["health_summary"] = {
            "online_percentage": (
                stats["by_status"].get("online", 0) / max(stats["total"], 1) * 100
            ),
            "offline_count": stats["by_status"].get("offline", 0),
            "unknown_count": stats["by_status"].get("unknown", 0)
        }
        
        stats["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        return stats
    
    async def _validate_target_creation(self, name: str, host: str, target_type: str, port: int) -> None:
        """Validate target creation data."""
        if not name or len(name.strip()) < 3:
            raise ValidationException("Target name must be at least 3 characters long")
        
        if not host:
            raise ValidationException("Host is required")
        
        # Validate host format (IP or hostname)
        if not self._is_valid_host(host):
            raise ValidationException("Invalid host format")
        
        if not target_type:
            raise ValidationException("Target type is required")
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValidationException("Port must be between 1 and 65535")
    
    def _is_valid_host(self, host: str) -> bool:
        """Validate host format."""
        try:
            # Try to parse as IP address
            ipaddress.ip_address(host)
            return True
        except ValueError:
            # Try as hostname
            try:
                socket.gethostbyname(host)
                return True
            except socket.gaierror:
                # Check if it's a valid hostname format
                if len(host) > 253:
                    return False
                
                allowed = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$")
                return bool(allowed.match(host))
    
    def _validate_bulk_update_data(self, update_data: Dict[str, Any]) -> None:
        """Validate bulk update data."""
        # Don't allow changing unique fields in bulk
        forbidden_fields = ["name", "host", "port"]
        for field in forbidden_fields:
            if field in update_data:
                raise ValidationException(f"Cannot bulk update field: {field}")
    
    async def _perform_connection_test(self, target: UniversalTarget) -> Dict[str, Any]:
        """Perform connection test to target."""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Simple TCP connection test
            future = asyncio.open_connection(target.host, target.port)
            reader, writer = await asyncio.wait_for(future, timeout=10.0)
            
            writer.close()
            await writer.wait_closed()
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                "success": True,
                "response_time": response_time,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Connection successful"
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Connection timeout",
                "response_time": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }