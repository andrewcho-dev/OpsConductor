"""
Target Service - Business logic for target management
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.target import Target, ConnectionMethod, Credential, TargetHealthCheck
from app.schemas.target import (
    TargetCreate, TargetUpdate, TargetResponse, TargetSummary,
    ConnectionTestResult, HealthCheckResult
)
from app.utils.encryption import encrypt_credential, decrypt_credential
from app.utils.connection_tester import ConnectionTester
from app.utils.serial_generator import generate_target_serial

logger = logging.getLogger(__name__)


class TargetService:
    """Service class for target operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.connection_tester = ConnectionTester()
    
    async def list_targets(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TargetSummary]:
        """List targets with filtering and pagination"""
        try:
            query = self.db.query(Target).options(
                joinedload(Target.connection_methods)
            )
            
            # Apply filters
            if filters:
                if filters.get('target_type'):
                    query = query.filter(Target.target_type == filters['target_type'])
                if filters.get('os_type'):
                    query = query.filter(Target.os_type == filters['os_type'])
                if filters.get('environment'):
                    query = query.filter(Target.environment == filters['environment'])
                if filters.get('status'):
                    query = query.filter(Target.status == filters['status'])
                if filters.get('health_status'):
                    query = query.filter(Target.health_status == filters['health_status'])
                if filters.get('tags'):
                    # Filter by tags (PostgreSQL JSONB contains)
                    for tag in filters['tags']:
                        query = query.filter(Target.tags.contains([tag]))
            
            # Apply search
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Target.name.ilike(search_term),
                        Target.description.ilike(search_term)
                    )
                )
            
            # Apply pagination
            targets = query.offset(skip).limit(limit).all()
            
            # Convert to summary format
            summaries = []
            for target in targets:
                primary_method = next(
                    (cm for cm in target.connection_methods if cm.is_primary and cm.is_active),
                    target.connection_methods[0] if target.connection_methods else None
                )
                
                summary = TargetSummary(
                    id=target.id,
                    target_uuid=target.target_uuid,
                    target_serial=target.target_serial,
                    name=target.name,
                    target_type=target.target_type,
                    os_type=target.os_type,
                    environment=target.environment,
                    status=target.status,
                    health_status=target.health_status,
                    is_active=target.is_active,
                    primary_host=primary_method.config.get('host') if primary_method else None,
                    primary_method_type=primary_method.method_type if primary_method else None,
                    created_at=target.created_at,
                    updated_at=target.updated_at
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to list targets: {e}")
            raise
    
    async def get_target_by_id(self, target_id: int) -> Optional[TargetResponse]:
        """Get a target by ID with full details"""
        try:
            target = self.db.query(Target).options(
                joinedload(Target.connection_methods).joinedload(ConnectionMethod.credentials)
            ).filter(Target.id == target_id).first()
            
            if not target:
                return None
            
            return TargetResponse.from_orm(target)
            
        except Exception as e:
            logger.error(f"Failed to get target {target_id}: {e}")
            raise
    
    async def create_target(
        self,
        target_data: TargetCreate,
        created_by: Optional[int] = None
    ) -> TargetResponse:
        """Create a new target with connection method and credentials"""
        try:
            # Check for duplicate IP address
            existing_target = await self._check_duplicate_ip(target_data.host)
            if existing_target:
                raise ValueError(f"IP address {target_data.host} is already in use by target: {existing_target.name}")
            
            # Generate unique serial
            target_serial = generate_target_serial()
            
            # Create target
            target = Target(
                target_serial=target_serial,
                name=target_data.name,
                target_type=target_data.target_type,
                description=target_data.description,
                os_type=target_data.os_type,
                environment=target_data.environment,
                location=target_data.location,
                data_center=target_data.data_center,
                region=target_data.region,
                tags=target_data.tags,
                metadata=target_data.metadata,
                created_by=created_by
            )
            
            self.db.add(target)
            self.db.flush()  # Get the target ID
            
            # Create primary connection method
            connection_config = {
                'host': target_data.host,
                'port': target_data.port or self._get_default_port(target_data.method_type)
            }
            
            connection_method = ConnectionMethod(
                target_id=target.id,
                method_type=target_data.method_type,
                method_name=f"{target_data.method_type}_{int(datetime.utcnow().timestamp())}",
                is_primary=True,
                is_active=True,
                priority=1,
                config=connection_config
            )
            
            self.db.add(connection_method)
            self.db.flush()  # Get the connection method ID
            
            # Create credentials if provided
            if target_data.username:
                credential_data = {
                    'username': target_data.username
                }
                
                if target_data.password:
                    credential_data['password'] = target_data.password
                    credential_type = 'password'
                elif target_data.ssh_key:
                    credential_data['ssh_key'] = target_data.ssh_key
                    if target_data.ssh_passphrase:
                        credential_data['ssh_passphrase'] = target_data.ssh_passphrase
                    credential_type = 'ssh_key'
                else:
                    raise ValueError("Either password or SSH key must be provided")
                
                # Encrypt credential data
                encrypted_data = encrypt_credential(credential_data)
                
                credential = Credential(
                    connection_method_id=connection_method.id,
                    credential_type=credential_type,
                    credential_name=f"{credential_type}_{target_data.username}",
                    username=target_data.username,
                    encrypted_data=encrypted_data,
                    is_primary=True,
                    is_active=True
                )
                
                self.db.add(credential)
            
            self.db.commit()
            
            # Return the created target with all relationships
            return await self.get_target_by_id(target.id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create target: {e}")
            raise
    
    async def update_target(
        self,
        target_id: int,
        target_data: TargetUpdate,
        updated_by: Optional[int] = None
    ) -> Optional[TargetResponse]:
        """Update a target"""
        try:
            target = self.db.query(Target).filter(Target.id == target_id).first()
            if not target:
                return None
            
            # Update fields
            update_data = target_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(target, field, value)
            
            target.updated_by = updated_by
            target.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return await self.get_target_by_id(target_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update target {target_id}: {e}")
            raise
    
    async def delete_target(self, target_id: int) -> bool:
        """Delete a target"""
        try:
            target = self.db.query(Target).filter(Target.id == target_id).first()
            if not target:
                return False
            
            # Soft delete - mark as inactive
            target.is_active = False
            target.status = "deleted"
            target.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete target {target_id}: {e}")
            raise
    
    async def test_target_connection(
        self,
        target_id: int,
        connection_method_id: Optional[int] = None,
        test_type: str = "basic",
        timeout: int = 30
    ) -> ConnectionTestResult:
        """Test connection to a target"""
        try:
            target = self.db.query(Target).options(
                joinedload(Target.connection_methods).joinedload(ConnectionMethod.credentials)
            ).filter(Target.id == target_id).first()
            
            if not target:
                return ConnectionTestResult(
                    success=False,
                    message=f"Target {target_id} not found",
                    tested_at=datetime.utcnow()
                )
            
            # Get connection method
            if connection_method_id:
                connection_method = next(
                    (cm for cm in target.connection_methods if cm.id == connection_method_id),
                    None
                )
            else:
                # Use primary method
                connection_method = next(
                    (cm for cm in target.connection_methods if cm.is_primary and cm.is_active),
                    target.connection_methods[0] if target.connection_methods else None
                )
            
            if not connection_method:
                return ConnectionTestResult(
                    success=False,
                    message="No connection method available",
                    tested_at=datetime.utcnow()
                )
            
            # Get credentials
            primary_credential = next(
                (cred for cred in connection_method.credentials if cred.is_primary and cred.is_active),
                connection_method.credentials[0] if connection_method.credentials else None
            )
            
            # Decrypt credentials if available
            credential_data = {}
            if primary_credential:
                credential_data = decrypt_credential(primary_credential.encrypted_data)
            
            # Perform connection test
            result = await self.connection_tester.test_connection(
                method_type=connection_method.method_type,
                config=connection_method.config,
                credentials=credential_data,
                test_type=test_type,
                timeout=timeout
            )
            
            # Store health check result
            health_check = TargetHealthCheck(
                target_id=target_id,
                connection_method_id=connection_method.id,
                check_type=f"connection_test_{test_type}",
                status="healthy" if result.success else "critical",
                response_time=int(result.response_time * 1000) if result.response_time else None,
                details=result.details,
                error_message=result.message if not result.success else None,
                checked_at=datetime.utcnow()
            )
            
            self.db.add(health_check)
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to test connection for target {target_id}: {e}")
            return ConnectionTestResult(
                success=False,
                message=f"Connection test failed: {str(e)}",
                tested_at=datetime.utcnow()
            )
    
    async def get_target_health(self, target_id: int) -> HealthCheckResult:
        """Get comprehensive health status for a target"""
        try:
            target = self.db.query(Target).filter(Target.id == target_id).first()
            if not target:
                raise ValueError(f"Target {target_id} not found")
            
            # Get recent health checks
            recent_checks = self.db.query(TargetHealthCheck).filter(
                and_(
                    TargetHealthCheck.target_id == target_id,
                    TargetHealthCheck.checked_at >= datetime.utcnow() - timedelta(hours=24)
                )
            ).order_by(TargetHealthCheck.checked_at.desc()).limit(10).all()
            
            # Determine overall status
            if not recent_checks:
                overall_status = "unknown"
            else:
                latest_check = recent_checks[0]
                overall_status = latest_check.status
            
            # Calculate average response time
            response_times = [check.response_time for check in recent_checks if check.response_time]
            avg_response_time = sum(response_times) / len(response_times) if response_times else None
            
            # Format check results
            checks = []
            for check in recent_checks:
                checks.append({
                    "type": check.check_type,
                    "status": check.status,
                    "response_time": check.response_time,
                    "checked_at": check.checked_at,
                    "error": check.error_message
                })
            
            return HealthCheckResult(
                target_id=target_id,
                status=overall_status,
                checks=checks,
                overall_response_time=avg_response_time / 1000 if avg_response_time else None,  # Convert to seconds
                checked_at=datetime.utcnow(),
                next_check_at=datetime.utcnow() + timedelta(minutes=30)  # Next scheduled check
            )
            
        except Exception as e:
            logger.error(f"Failed to get health for target {target_id}: {e}")
            raise
    
    async def bulk_test_connections(
        self,
        target_ids: List[int],
        test_options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Test connections to multiple targets"""
        results = []
        
        # Limit concurrent tests
        semaphore = asyncio.Semaphore(5)
        
        async def test_single_target(target_id: int):
            async with semaphore:
                try:
                    result = await self.test_target_connection(
                        target_id=target_id,
                        test_type=test_options.get("test_type", "basic"),
                        timeout=test_options.get("timeout", 30)
                    )
                    return {
                        "target_id": target_id,
                        "success": result.success,
                        "message": result.message,
                        "response_time": result.response_time
                    }
                except Exception as e:
                    return {
                        "target_id": target_id,
                        "success": False,
                        "message": str(e),
                        "response_time": None
                    }
        
        # Run tests concurrently
        tasks = [test_single_target(target_id) for target_id in target_ids]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def bulk_update_targets(
        self,
        target_ids: List[int],
        update_data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Update multiple targets with the same data"""
        results = []
        
        for target_id in target_ids:
            try:
                target_update = TargetUpdate(**update_data)
                updated_target = await self.update_target(
                    target_id=target_id,
                    target_data=target_update,
                    updated_by=updated_by
                )
                
                if updated_target:
                    results.append({
                        "target_id": target_id,
                        "success": True,
                        "message": "Target updated successfully"
                    })
                else:
                    results.append({
                        "target_id": target_id,
                        "success": False,
                        "message": "Target not found"
                    })
                    
            except Exception as e:
                results.append({
                    "target_id": target_id,
                    "success": False,
                    "message": str(e)
                })
        
        return results
    
    async def get_targets_stats(self) -> Dict[str, Any]:
        """Get target statistics"""
        try:
            total_targets = self.db.query(Target).filter(Target.is_active == True).count()
            
            # Count by status
            status_counts = self.db.query(
                Target.status,
                func.count(Target.id)
            ).filter(Target.is_active == True).group_by(Target.status).all()
            
            # Count by health status
            health_counts = self.db.query(
                Target.health_status,
                func.count(Target.id)
            ).filter(Target.is_active == True).group_by(Target.health_status).all()
            
            # Count by OS type
            os_counts = self.db.query(
                Target.os_type,
                func.count(Target.id)
            ).filter(Target.is_active == True).group_by(Target.os_type).all()
            
            # Count by environment
            env_counts = self.db.query(
                Target.environment,
                func.count(Target.id)
            ).filter(Target.is_active == True).group_by(Target.environment).all()
            
            return {
                "total_targets": total_targets,
                "by_status": {status: count for status, count in status_counts},
                "by_health_status": {health: count for health, count in health_counts},
                "by_os_type": {os_type: count for os_type, count in os_counts},
                "by_environment": {env: count for env, count in env_counts},
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get targets stats: {e}")
            raise
    
    async def validate_targets_exist(self, target_ids: List[int]) -> Dict[str, Any]:
        """Validate that targets exist and are accessible"""
        try:
            existing_targets = self.db.query(Target.id).filter(
                and_(
                    Target.id.in_(target_ids),
                    Target.is_active == True
                )
            ).all()
            
            existing_ids = [t.id for t in existing_targets]
            missing_ids = [tid for tid in target_ids if tid not in existing_ids]
            
            return {
                "valid": len(missing_ids) == 0,
                "total_requested": len(target_ids),
                "found": len(existing_ids),
                "missing": len(missing_ids),
                "existing_ids": existing_ids,
                "missing_ids": missing_ids
            }
            
        except Exception as e:
            logger.error(f"Failed to validate targets: {e}")
            raise
    
    # Helper methods
    
    async def _check_duplicate_ip(self, ip_address: str) -> Optional[Target]:
        """Check if IP address is already in use"""
        targets = self.db.query(Target).options(
            joinedload(Target.connection_methods)
        ).filter(Target.is_active == True).all()
        
        for target in targets:
            for method in target.connection_methods:
                if method.is_active and method.config.get('host') == ip_address:
                    return target
        
        return None
    
    def _get_default_port(self, method_type: str) -> int:
        """Get default port for connection method type"""
        default_ports = {
            'ssh': 22,
            'winrm': 5985,
            'telnet': 23,
            'mysql': 3306,
            'postgresql': 5432,
            'mssql': 1433,
            'oracle': 1521,
            'mongodb': 27017,
            'redis': 6379,
            'elasticsearch': 9200
        }
        return default_ports.get(method_type, 22)