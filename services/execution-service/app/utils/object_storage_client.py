"""
Object Storage Client for OpsConductor Execution Service
Handles MinIO/S3-compatible storage operations for job artifacts
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

from ..core.config import settings

logger = logging.getLogger(__name__)


class ObjectStorageClient:
    """
    S3/MinIO client for storing and retrieving job execution artifacts
    """
    
    def __init__(self):
        if not MINIO_AVAILABLE:
            raise ImportError("MinIO client not available. Install with: pip install minio")
            
        self.enabled = settings.object_storage_enabled
        self.size_threshold = self._parse_size(settings.object_storage_size_threshold)
        
        if self.enabled:
            # Initialize MinIO client
            endpoint = settings.minio_endpoint.replace('http://', '').replace('https://', '')
            self.client = Minio(
                endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
                region=settings.minio_region
            )
            
            # Default buckets
            self.buckets = {
                'executions': settings.object_storage_executions_bucket,
                'artifacts': settings.object_storage_artifacts_bucket,
                'logs': settings.object_storage_logs_bucket,
                'temp': settings.object_storage_temp_bucket
            }
            
            # Ensure buckets exist
            self._ensure_buckets_exist()
        else:
            self.client = None
            logger.info("Object storage disabled - using filesystem storage")
    
    def _parse_size(self, size_str: str) -> int:
        """Convert size string (64KB, 10MB, etc.) to bytes"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)  # Assume bytes
    
    def _ensure_buckets_exist(self):
        """Create default buckets if they don't exist"""
        if not self.enabled:
            return
            
        for bucket_type, bucket_name in self.buckets.items():
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created bucket: {bucket_name}")
            except S3Error as e:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
    
    def should_use_object_storage(self, data_size: int) -> bool:
        """Determine if data should go to object storage vs database"""
        return self.enabled and data_size > self.size_threshold
    
    def generate_object_key(self, 
                          job_execution_id: int,
                          artifact_name: str, 
                          artifact_type: str = "artifact") -> str:
        """
        Generate a structured object key for storage
        Format: executions/{year}/{month}/{execution_id}/{artifact_type}/{artifact_name}
        """
        now = datetime.utcnow()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        
        # Sanitize artifact name
        safe_name = "".join(c for c in artifact_name if c.isalnum() or c in '-_.')
        
        return f"executions/{year}/{month}/{job_execution_id}/{artifact_type}/{safe_name}"
    
    def upload_artifact(self, 
                       job_execution_id: int,
                       artifact_name: str,
                       data: bytes,
                       artifact_type: str = "artifact",
                       bucket_type: str = "artifacts",
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload artifact data to object storage
        
        Args:
            job_execution_id: ID of the job execution
            artifact_name: Name of the artifact
            data: Raw bytes to store
            artifact_type: Type of artifact (log, file, report, etc.)
            bucket_type: Which bucket to use (artifacts, logs, executions, temp)
            metadata: Additional metadata to store
        
        Returns:
            Dict with object_key, bucket_name, checksum, storage_url, etc.
        """
        if not self.enabled:
            raise ValueError("Object storage is disabled")
        
        # Generate object key and select bucket
        object_key = self.generate_object_key(job_execution_id, artifact_name, artifact_type)
        bucket_name = self.buckets.get(bucket_type, self.buckets['artifacts'])
        
        # Calculate checksum
        checksum = hashlib.sha256(data).hexdigest()
        
        # Prepare metadata
        object_metadata = {
            'job-execution-id': str(job_execution_id),
            'artifact-type': artifact_type,
            'artifact-name': artifact_name,
            'uploaded-by': 'execution-service',
            'upload-timestamp': datetime.utcnow().isoformat(),
            'checksum-sha256': checksum,
        }
        
        if metadata:
            object_metadata.update({f"custom-{k}": str(v) for k, v in metadata.items()})
        
        try:
            # Upload to MinIO
            from io import BytesIO
            data_stream = BytesIO(data)
            
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_key,
                data=data_stream,
                length=len(data),
                metadata=object_metadata
            )
            
            # Generate storage URL
            storage_url = f"{settings.minio_endpoint}/{bucket_name}/{object_key}"
            
            logger.info(f"Uploaded artifact {artifact_name} to {bucket_name}/{object_key}")
            
            return {
                'storage_type': 'object_storage',
                'object_key': object_key,
                'bucket_name': bucket_name,
                'storage_url': storage_url,
                'file_size': len(data),
                'checksum': checksum,
                'metadata': metadata or {}
            }
            
        except S3Error as e:
            logger.error(f"Failed to upload {artifact_name}: {e}")
            raise
    
    def download_artifact(self, bucket_name: str, object_key: str) -> bytes:
        """Download artifact data from object storage"""
        if not self.enabled:
            raise ValueError("Object storage is disabled")
        
        try:
            response = self.client.get_object(bucket_name, object_key)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded {len(data)} bytes from {bucket_name}/{object_key}")
            return data
            
        except S3Error as e:
            logger.error(f"Failed to download {bucket_name}/{object_key}: {e}")
            raise
    
    def get_presigned_url(self, 
                         bucket_name: str, 
                         object_key: str,
                         expires_in_hours: int = 1) -> str:
        """Generate a presigned URL for direct download"""
        if not self.enabled:
            raise ValueError("Object storage is disabled")
        
        try:
            expires = timedelta(hours=expires_in_hours)
            url = self.client.presigned_get_object(bucket_name, object_key, expires=expires)
            
            logger.info(f"Generated presigned URL for {bucket_name}/{object_key}, expires in {expires_in_hours}h")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_artifact(self, bucket_name: str, object_key: str) -> bool:
        """Delete artifact from object storage"""
        if not self.enabled:
            return False
        
        try:
            self.client.remove_object(bucket_name, object_key)
            logger.info(f"Deleted {bucket_name}/{object_key}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete {bucket_name}/{object_key}: {e}")
            return False
    
    def list_artifacts(self, 
                      job_execution_id: int,
                      bucket_type: str = "artifacts") -> List[Dict[str, Any]]:
        """List all artifacts for a job execution"""
        if not self.enabled:
            return []
        
        bucket_name = self.buckets.get(bucket_type, self.buckets['artifacts'])
        prefix = f"executions/"
        
        artifacts = []
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            
            for obj in objects:
                if f"/{job_execution_id}/" in obj.object_name:
                    artifacts.append({
                        'object_key': obj.object_name,
                        'bucket_name': bucket_name,
                        'size': obj.size,
                        'last_modified': obj.last_modified,
                        'etag': obj.etag
                    })
            
            logger.info(f"Found {len(artifacts)} artifacts for execution {job_execution_id}")
            return artifacts
            
        except S3Error as e:
            logger.error(f"Failed to list artifacts: {e}")
            return []
    
    def get_bucket_stats(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket usage statistics"""
        if not self.enabled:
            return {}
        
        try:
            objects = self.client.list_objects(bucket_name, recursive=True)
            
            total_size = 0
            object_count = 0
            
            for obj in objects:
                total_size += obj.size or 0
                object_count += 1
            
            return {
                'bucket_name': bucket_name,
                'object_count': object_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except S3Error as e:
            logger.error(f"Failed to get bucket stats for {bucket_name}: {e}")
            return {}
    
    def cleanup_expired_objects(self, bucket_name: str, retention_days: int = 30) -> int:
        """Clean up objects older than retention period"""
        if not self.enabled:
            return 0
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted_count = 0
        
        try:
            objects = self.client.list_objects(bucket_name, recursive=True)
            
            for obj in objects:
                if obj.last_modified < cutoff_date:
                    self.client.remove_object(bucket_name, obj.object_name)
                    deleted_count += 1
                    logger.info(f"Deleted expired object: {obj.object_name}")
            
            logger.info(f"Cleaned up {deleted_count} expired objects from {bucket_name}")
            return deleted_count
            
        except S3Error as e:
            logger.error(f"Failed to cleanup {bucket_name}: {e}")
            return 0


# Global instance
object_storage = ObjectStorageClient()


# Usage Examples
def store_job_output(job_execution_id: int, stdout: str, stderr: str) -> Dict[str, Any]:
    """
    Example: Store job stdout/stderr output
    """
    results = {}
    
    # Store stdout
    if stdout and len(stdout.encode()) > object_storage.size_threshold:
        stdout_data = stdout.encode('utf-8')
        results['stdout'] = object_storage.upload_artifact(
            job_execution_id=job_execution_id,
            artifact_name=f"stdout_{job_execution_id}.log",
            data=stdout_data,
            artifact_type="log",
            bucket_type="logs"
        )
    else:
        results['stdout'] = {'storage_type': 'database', 'content': stdout}
    
    # Store stderr  
    if stderr and len(stderr.encode()) > object_storage.size_threshold:
        stderr_data = stderr.encode('utf-8')
        results['stderr'] = object_storage.upload_artifact(
            job_execution_id=job_execution_id,
            artifact_name=f"stderr_{job_execution_id}.log", 
            data=stderr_data,
            artifact_type="log",
            bucket_type="logs"
        )
    else:
        results['stderr'] = {'storage_type': 'database', 'content': stderr}
    
    return results


def store_generated_file(job_execution_id: int, 
                        filename: str, 
                        file_data: bytes,
                        description: str = None) -> Dict[str, Any]:
    """
    Example: Store a file generated during job execution
    """
    metadata = {}
    if description:
        metadata['description'] = description
    
    return object_storage.upload_artifact(
        job_execution_id=job_execution_id,
        artifact_name=filename,
        data=file_data,
        artifact_type="file",
        bucket_type="artifacts",
        metadata=metadata
    )


def retrieve_artifact_content(bucket_name: str, object_key: str) -> bytes:
    """
    Example: Retrieve artifact content
    """
    return object_storage.download_artifact(bucket_name, object_key)


def get_artifact_download_url(bucket_name: str, object_key: str) -> str:
    """
    Example: Get a signed URL for direct download
    """
    return object_storage.get_presigned_url(bucket_name, object_key, expires_in_hours=24)