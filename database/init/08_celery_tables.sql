-- Celery Task Management Tables
-- This creates tables for Celery task history and metrics

-- Create enum types for Celery
CREATE TYPE task_status AS ENUM ('pending', 'started', 'retry', 'failure', 'success', 'revoked');

-- Celery Task History
CREATE TABLE IF NOT EXISTS celery_task_history (
    id SERIAL PRIMARY KEY,
    task_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    task_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'TASK-' || LPAD(nextval('celery_task_history_id_seq')::text, 8, '0'),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status task_status NOT NULL DEFAULT 'pending',
    result TEXT,
    traceback TEXT,
    args JSONB,
    kwargs JSONB,
    eta TIMESTAMP WITH TIME ZONE,
    expires TIMESTAMP WITH TIME ZONE,
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    queue VARCHAR(100),
    routing_key VARCHAR(100),
    worker VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    runtime_seconds DECIMAL(10,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Celery Metrics Snapshots
CREATE TABLE IF NOT EXISTS celery_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    snapshot_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'SNAP-' || LPAD(nextval('celery_metrics_snapshots_id_seq')::text, 8, '0'),
    worker_name VARCHAR(255) NOT NULL,
    active_tasks INTEGER DEFAULT 0,
    processed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    retried_tasks INTEGER DEFAULT 0,
    queue_lengths JSONB,
    worker_stats JSONB,
    system_load JSONB,
    memory_usage JSONB,
    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_celery_task_history_task_id ON celery_task_history(task_id);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_task_name ON celery_task_history(task_name);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_status ON celery_task_history(status);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_queue ON celery_task_history(queue);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_worker ON celery_task_history(worker);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_started_at ON celery_task_history(started_at);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_completed_at ON celery_task_history(completed_at);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_task_uuid ON celery_task_history(task_uuid);
CREATE INDEX IF NOT EXISTS idx_celery_task_history_task_serial ON celery_task_history(task_serial);

CREATE INDEX IF NOT EXISTS idx_celery_metrics_snapshots_worker_name ON celery_metrics_snapshots(worker_name);
CREATE INDEX IF NOT EXISTS idx_celery_metrics_snapshots_snapshot_time ON celery_metrics_snapshots(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_celery_metrics_snapshots_snapshot_uuid ON celery_metrics_snapshots(snapshot_uuid);
CREATE INDEX IF NOT EXISTS idx_celery_metrics_snapshots_snapshot_serial ON celery_metrics_snapshots(snapshot_serial);