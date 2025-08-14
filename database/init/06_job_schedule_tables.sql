-- Job Scheduling Tables
-- This creates tables for job scheduling and recurring job management

-- Create enum types for job scheduling
CREATE TYPE schedule_type AS ENUM ('cron', 'interval', 'one_time');
CREATE TYPE schedule_status AS ENUM ('active', 'paused', 'disabled', 'expired');
CREATE TYPE execution_status_schedule AS ENUM ('scheduled', 'running', 'completed', 'failed', 'skipped');

-- Job Schedules
CREATE TABLE IF NOT EXISTS job_schedules (
    id SERIAL PRIMARY KEY,
    schedule_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    schedule_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'JSCHED-' || LPAD(nextval('job_schedules_id_seq')::text, 8, '0'),
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_type schedule_type NOT NULL DEFAULT 'cron',
    cron_expression VARCHAR(100),
    interval_seconds INTEGER,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    status schedule_status NOT NULL DEFAULT 'active',
    max_runs INTEGER,
    current_runs INTEGER DEFAULT 0,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    schedule_config JSONB
);

-- Schedule Executions
CREATE TABLE IF NOT EXISTS schedule_executions (
    id SERIAL PRIMARY KEY,
    execution_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    execution_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'SEXEC-' || LPAD(nextval('schedule_executions_id_seq')::text, 8, '0'),
    job_schedule_id INTEGER NOT NULL REFERENCES job_schedules(id) ON DELETE CASCADE,
    job_execution_id INTEGER REFERENCES job_executions(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status execution_status_schedule NOT NULL DEFAULT 'scheduled',
    result_summary TEXT,
    error_message TEXT,
    execution_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_job_schedules_job_id ON job_schedules(job_id);
CREATE INDEX IF NOT EXISTS idx_job_schedules_status ON job_schedules(status);
CREATE INDEX IF NOT EXISTS idx_job_schedules_is_active ON job_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_job_schedules_next_run_at ON job_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_job_schedules_schedule_type ON job_schedules(schedule_type);
CREATE INDEX IF NOT EXISTS idx_job_schedules_created_by ON job_schedules(created_by);
CREATE INDEX IF NOT EXISTS idx_job_schedules_schedule_uuid ON job_schedules(schedule_uuid);
CREATE INDEX IF NOT EXISTS idx_job_schedules_schedule_serial ON job_schedules(schedule_serial);

CREATE INDEX IF NOT EXISTS idx_schedule_executions_job_schedule_id ON schedule_executions(job_schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_executions_job_execution_id ON schedule_executions(job_execution_id);
CREATE INDEX IF NOT EXISTS idx_schedule_executions_status ON schedule_executions(status);
CREATE INDEX IF NOT EXISTS idx_schedule_executions_scheduled_at ON schedule_executions(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_schedule_executions_execution_uuid ON schedule_executions(execution_uuid);
CREATE INDEX IF NOT EXISTS idx_schedule_executions_execution_serial ON schedule_executions(execution_serial);