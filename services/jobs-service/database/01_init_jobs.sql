-- Jobs Service Database Initialization

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS jobs_db;
\c jobs_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Job status enum
CREATE TYPE job_status AS ENUM ('draft', 'active', 'paused', 'completed', 'cancelled', 'failed');
CREATE TYPE schedule_type AS ENUM ('immediate', 'scheduled', 'recurring', 'cron');
CREATE TYPE action_type AS ENUM ('shell_command', 'script', 'file_transfer', 'service_restart', 'custom');

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    job_type VARCHAR(50) DEFAULT 'shell_command',
    status job_status DEFAULT 'draft',
    schedule_type schedule_type DEFAULT 'immediate',
    cron_expression VARCHAR(100),
    scheduled_time TIMESTAMP WITH TIME ZONE,
    priority INTEGER DEFAULT 5, -- 1-10, higher is more priority
    timeout_seconds INTEGER DEFAULT 3600,
    max_retries INTEGER DEFAULT 0,
    retry_delay_seconds INTEGER DEFAULT 60,
    config JSONB, -- Job configuration (commands, scripts, etc.)
    tags TEXT[],
    metadata JSONB,
    environment_variables JSONB,
    created_by INTEGER, -- User ID from user service
    updated_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job actions table (for multi-step jobs)
CREATE TABLE IF NOT EXISTS job_actions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    action_type action_type NOT NULL,
    order_index INTEGER NOT NULL,
    config JSONB NOT NULL, -- Action-specific configuration
    depends_on INTEGER[], -- Array of action IDs this depends on
    timeout_seconds INTEGER,
    retry_on_failure BOOLEAN DEFAULT FALSE,
    continue_on_failure BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job targets table (which targets to run job on)
CREATE TABLE IF NOT EXISTS job_targets (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL, -- Reference to targets service
    target_group_id INTEGER, -- Reference to target groups service
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,
    UNIQUE(job_id, target_id)
);

-- Job schedules table (for recurring jobs)
CREATE TABLE IF NOT EXISTS job_schedules (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    name VARCHAR(200),
    description TEXT,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    next_run_time TIMESTAMP WITH TIME ZONE,
    last_run_time TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    max_runs INTEGER, -- NULL for unlimited
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job templates table
CREATE TABLE IF NOT EXISTS job_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),
    template_data JSONB NOT NULL, -- Job configuration template
    variables JSONB, -- Template variables with defaults
    tags TEXT[],
    is_public BOOLEAN DEFAULT FALSE,
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job approval workflows table
CREATE TABLE IF NOT EXISTS job_approvals (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    required_approvals INTEGER DEFAULT 1,
    current_approvals INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    requested_by INTEGER NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    metadata JSONB
);

-- Job approval entries table
CREATE TABLE IF NOT EXISTS job_approval_entries (
    id SERIAL PRIMARY KEY,
    approval_id INTEGER NOT NULL REFERENCES job_approvals(id) ON DELETE CASCADE,
    approver_id INTEGER NOT NULL, -- User ID
    status VARCHAR(20) NOT NULL, -- approved, rejected
    comment TEXT,
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_schedule_type ON jobs(schedule_type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_jobs_uuid ON jobs(uuid);
CREATE INDEX IF NOT EXISTS idx_job_actions_job_id ON job_actions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_actions_order ON job_actions(job_id, order_index);
CREATE INDEX IF NOT EXISTS idx_job_targets_job_id ON job_targets(job_id);
CREATE INDEX IF NOT EXISTS idx_job_targets_target_id ON job_targets(target_id);
CREATE INDEX IF NOT EXISTS idx_job_schedules_job_id ON job_schedules(job_id);
CREATE INDEX IF NOT EXISTS idx_job_schedules_active ON job_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_job_schedules_next_run ON job_schedules(next_run_time);
CREATE INDEX IF NOT EXISTS idx_job_templates_category ON job_templates(category);
CREATE INDEX IF NOT EXISTS idx_job_templates_public ON job_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_job_approvals_job_id ON job_approvals(job_id);
CREATE INDEX IF NOT EXISTS idx_job_approvals_status ON job_approvals(status);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_job_actions_updated_at BEFORE UPDATE ON job_actions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_job_schedules_updated_at BEFORE UPDATE ON job_schedules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_job_templates_updated_at BEFORE UPDATE ON job_templates FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();