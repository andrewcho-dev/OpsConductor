-- Migration: Add Celery Task Monitoring Tables
-- Description: Adds tables for tracking Celery task history and metrics snapshots
-- Date: 2025-01-08

-- Create celery_task_history table for storing completed task information
CREATE TABLE celery_task_history (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    worker_name VARCHAR(255),
    queue_name VARCHAR(100),
    
    -- Timing information
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration FLOAT,
    
    -- Status and result
    status VARCHAR(50),
    result TEXT,
    exception TEXT,
    traceback TEXT,
    
    -- Task details
    args TEXT,
    kwargs TEXT,
    retries INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create celery_metrics_snapshots table for historical metrics
CREATE TABLE celery_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Task metrics
    active_tasks INTEGER DEFAULT 0,
    scheduled_tasks INTEGER DEFAULT 0,
    completed_tasks_last_hour INTEGER DEFAULT 0,
    failed_tasks_last_hour INTEGER DEFAULT 0,
    tasks_per_minute FLOAT DEFAULT 0.0,
    avg_task_duration FLOAT DEFAULT 0.0,
    
    -- Worker metrics
    total_workers INTEGER DEFAULT 0,
    active_workers INTEGER DEFAULT 0,
    avg_worker_load FLOAT DEFAULT 0.0,
    
    -- Queue metrics (JSON string)
    queue_depths TEXT,
    
    -- Error rates
    error_rate FLOAT DEFAULT 0.0,
    success_rate FLOAT DEFAULT 100.0
);

-- Create indexes for performance
CREATE INDEX idx_celery_task_history_task_id ON celery_task_history(task_id);
CREATE INDEX idx_celery_task_history_task_name ON celery_task_history(task_name);
CREATE INDEX idx_celery_task_history_worker_name ON celery_task_history(worker_name);
CREATE INDEX idx_celery_task_history_queue_name ON celery_task_history(queue_name);
CREATE INDEX idx_celery_task_history_status ON celery_task_history(status);
CREATE INDEX idx_celery_task_history_completed_at ON celery_task_history(completed_at);
CREATE INDEX idx_celery_task_history_created_at ON celery_task_history(created_at);

CREATE INDEX idx_celery_metrics_snapshots_timestamp ON celery_metrics_snapshots(timestamp);

-- Comments for documentation
COMMENT ON TABLE celery_task_history IS 'Stores completed Celery task information for metrics and monitoring';
COMMENT ON TABLE celery_metrics_snapshots IS 'Stores periodic snapshots of Celery metrics for historical charts';

COMMENT ON COLUMN celery_task_history.task_id IS 'Unique Celery task ID';
COMMENT ON COLUMN celery_task_history.task_name IS 'Name of the Celery task';
COMMENT ON COLUMN celery_task_history.duration IS 'Task execution duration in seconds';
COMMENT ON COLUMN celery_task_history.status IS 'Task status: SUCCESS, FAILURE, RETRY, REVOKED';

COMMENT ON COLUMN celery_metrics_snapshots.queue_depths IS 'JSON object with queue names and their depths';
COMMENT ON COLUMN celery_metrics_snapshots.error_rate IS 'Percentage of failed tasks';
COMMENT ON COLUMN celery_metrics_snapshots.success_rate IS 'Percentage of successful tasks';