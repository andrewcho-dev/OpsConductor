-- Execution Service Database Initialization

-- Note: Database is already created by POSTGRES_DB environment variable
-- So we just connect to it and set up the schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Execution status enum
CREATE TYPE execution_status AS ENUM ('queued', 'running', 'completed', 'failed', 'cancelled', 'timeout');
CREATE TYPE execution_priority AS ENUM ('low', 'normal', 'high', 'critical');

-- Job executions table
CREATE TABLE IF NOT EXISTS job_executions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_id INTEGER NOT NULL, -- Reference to jobs service
    job_name VARCHAR(200),
    target_id INTEGER NOT NULL, -- Reference to targets service
    target_name VARCHAR(200),
    target_hostname VARCHAR(255),
    status execution_status DEFAULT 'queued',
    priority execution_priority DEFAULT 'normal',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    exit_code INTEGER,
    stdout_log TEXT,
    stderr_log TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 0,
    timeout_seconds INTEGER DEFAULT 3600,
    config JSONB, -- Execution configuration
    environment_variables JSONB,
    metadata JSONB,
    created_by INTEGER, -- User ID who triggered execution
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Action executions table (for multi-step jobs)
CREATE TABLE IF NOT EXISTS action_executions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_execution_id INTEGER NOT NULL REFERENCES job_executions(id) ON DELETE CASCADE,
    action_id INTEGER NOT NULL, -- Reference to job_actions
    action_name VARCHAR(200),
    order_index INTEGER NOT NULL,
    status execution_status DEFAULT 'queued',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    exit_code INTEGER,
    stdout_log TEXT,
    stderr_log TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    config JSONB, -- Action-specific configuration
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    deleted_by INTEGER
);

-- Execution queue table
CREATE TABLE IF NOT EXISTS execution_queue (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_execution_id INTEGER NOT NULL REFERENCES job_executions(id) ON DELETE CASCADE,
    priority execution_priority DEFAULT 'normal',
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    worker_id VARCHAR(100), -- Which worker picked up the job
    locked_at TIMESTAMP WITH TIME ZONE, -- When worker locked the job
    lock_expires_at TIMESTAMP WITH TIME ZONE, -- Lock expiration
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Execution workers table (track active workers)
CREATE TABLE IF NOT EXISTS execution_workers (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(100) UNIQUE NOT NULL,
    hostname VARCHAR(255),
    pid INTEGER,
    status VARCHAR(20) DEFAULT 'active', -- active, idle, busy, offline
    max_concurrent_jobs INTEGER DEFAULT 5,
    current_job_count INTEGER DEFAULT 0,
    capabilities TEXT[], -- What types of jobs this worker can handle
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- File transfers table (for jobs that involve file operations)
CREATE TABLE IF NOT EXISTS file_transfers (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_execution_id INTEGER NOT NULL REFERENCES job_executions(id) ON DELETE CASCADE,
    transfer_type VARCHAR(20) NOT NULL, -- upload, download
    source_path TEXT NOT NULL,
    destination_path TEXT NOT NULL,
    file_size BIGINT,
    bytes_transferred BIGINT DEFAULT 0,
    transfer_rate_bps BIGINT, -- bytes per second
    status VARCHAR(20) DEFAULT 'pending', -- pending, transferring, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    checksum VARCHAR(64), -- SHA256 checksum
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Execution artifacts table (store execution outputs, files, etc.)
CREATE TABLE IF NOT EXISTS execution_artifacts (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_execution_id INTEGER NOT NULL REFERENCES job_executions(id) ON DELETE CASCADE,
    action_execution_id INTEGER REFERENCES action_executions(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL, -- log, file, screenshot, report, etc.
    name VARCHAR(200) NOT NULL,
    description TEXT,
    storage_type VARCHAR(20) DEFAULT 'filesystem', -- filesystem, object_storage, database
    file_path TEXT, -- Path to stored file (filesystem)
    object_key TEXT, -- Object storage key (S3/MinIO path)
    bucket_name VARCHAR(100), -- Object storage bucket
    storage_url TEXT, -- Full URL to object (for CDN/direct access)
    file_size BIGINT,
    mime_type VARCHAR(100),
    content TEXT, -- For small text artifacts (< 64KB)
    checksum VARCHAR(64), -- SHA256 checksum for integrity
    compression VARCHAR(20), -- gzip, none
    encryption_key VARCHAR(100), -- For client-side encryption
    retention_policy VARCHAR(50), -- temporary, permanent, archived
    expires_at TIMESTAMP WITH TIME ZONE, -- For automatic cleanup
    access_count INTEGER DEFAULT 0, -- Track usage
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Resource usage tracking
CREATE TABLE IF NOT EXISTS execution_resources (
    id SERIAL PRIMARY KEY,
    job_execution_id INTEGER NOT NULL REFERENCES job_executions(id) ON DELETE CASCADE,
    worker_id VARCHAR(100),
    cpu_percent DECIMAL(5,2),
    memory_mb INTEGER,
    disk_io_mb INTEGER,
    network_io_mb INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Object storage buckets configuration
CREATE TABLE IF NOT EXISTS object_storage_buckets (
    id SERIAL PRIMARY KEY,
    bucket_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    bucket_type VARCHAR(50) NOT NULL, -- executions, artifacts, logs, backups, temp
    retention_days INTEGER, -- Auto-delete objects after N days
    lifecycle_policy JSONB, -- Object lifecycle rules
    encryption_enabled BOOLEAN DEFAULT TRUE,
    versioning_enabled BOOLEAN DEFAULT FALSE,
    public_access BOOLEAN DEFAULT FALSE,
    max_object_size BIGINT, -- Max size per object in bytes
    total_size_limit BIGINT, -- Total bucket size limit
    current_size BIGINT DEFAULT 0, -- Current usage
    object_count INTEGER DEFAULT 0, -- Number of objects
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Object storage access logs (for auditing)
CREATE TABLE IF NOT EXISTS object_storage_access_logs (
    id SERIAL PRIMARY KEY,
    artifact_id INTEGER REFERENCES execution_artifacts(id),
    bucket_name VARCHAR(100),
    object_key TEXT,
    operation VARCHAR(20), -- upload, download, delete, list
    user_id INTEGER, -- Who accessed it
    client_ip INET,
    user_agent TEXT,
    bytes_transferred BIGINT,
    status_code INTEGER, -- HTTP status code
    error_message TEXT,
    access_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_target_id ON job_executions(target_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_created_by ON job_executions(created_by);
CREATE INDEX IF NOT EXISTS idx_job_executions_started_at ON job_executions(started_at);
CREATE INDEX IF NOT EXISTS idx_job_executions_uuid ON job_executions(uuid);
CREATE INDEX IF NOT EXISTS idx_job_executions_deleted_at ON job_executions(deleted_at);
CREATE INDEX IF NOT EXISTS idx_action_executions_job_execution_id ON action_executions(job_execution_id);
CREATE INDEX IF NOT EXISTS idx_action_executions_status ON action_executions(status);
CREATE INDEX IF NOT EXISTS idx_action_executions_deleted_at ON action_executions(deleted_at);
CREATE INDEX IF NOT EXISTS idx_execution_queue_priority ON execution_queue(priority);
CREATE INDEX IF NOT EXISTS idx_execution_queue_scheduled_for ON execution_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_execution_queue_worker_id ON execution_queue(worker_id);
CREATE INDEX IF NOT EXISTS idx_execution_workers_worker_id ON execution_workers(worker_id);
CREATE INDEX IF NOT EXISTS idx_execution_workers_status ON execution_workers(status);
CREATE INDEX IF NOT EXISTS idx_file_transfers_job_execution_id ON file_transfers(job_execution_id);
CREATE INDEX IF NOT EXISTS idx_file_transfers_status ON file_transfers(status);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_job_execution_id ON execution_artifacts(job_execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_type ON execution_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_storage_type ON execution_artifacts(storage_type);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_bucket_name ON execution_artifacts(bucket_name);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_object_key ON execution_artifacts(object_key);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_expires_at ON execution_artifacts(expires_at);
CREATE INDEX IF NOT EXISTS idx_execution_artifacts_retention_policy ON execution_artifacts(retention_policy);
CREATE INDEX IF NOT EXISTS idx_execution_resources_job_execution_id ON execution_resources(job_execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_resources_recorded_at ON execution_resources(recorded_at);
CREATE INDEX IF NOT EXISTS idx_object_storage_buckets_type ON object_storage_buckets(bucket_type);
CREATE INDEX IF NOT EXISTS idx_object_storage_access_logs_artifact_id ON object_storage_access_logs(artifact_id);
CREATE INDEX IF NOT EXISTS idx_object_storage_access_logs_bucket_operation ON object_storage_access_logs(bucket_name, operation);
CREATE INDEX IF NOT EXISTS idx_object_storage_access_logs_access_time ON object_storage_access_logs(access_time);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_job_executions_updated_at BEFORE UPDATE ON job_executions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_action_executions_updated_at BEFORE UPDATE ON action_executions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_object_storage_buckets_updated_at BEFORE UPDATE ON object_storage_buckets FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Insert default object storage buckets
INSERT INTO object_storage_buckets (bucket_name, description, bucket_type, retention_days, encryption_enabled, versioning_enabled, max_object_size, total_size_limit) VALUES 
('opsconductor-executions', 'Job execution logs and outputs', 'executions', 365, true, false, 1073741824, 107374182400), -- 1GB per object, 100GB total
('opsconductor-artifacts', 'Job artifacts and generated files', 'artifacts', 730, true, true, 5368709120, 536870912000), -- 5GB per object, 500GB total  
('opsconductor-logs', 'Detailed execution logs', 'logs', 90, true, false, 104857600, 10737418240), -- 100MB per object, 10GB total
('opsconductor-temp', 'Temporary files and processing data', 'temp', 7, false, false, 1073741824, 53687091200), -- 1GB per object, 50GB total
('opsconductor-backups', 'Database and configuration backups', 'backups', 2555, true, true, 10737418240, 1073741824000) -- 10GB per object, 1TB total
ON CONFLICT (bucket_name) DO NOTHING;