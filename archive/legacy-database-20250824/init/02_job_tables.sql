-- Job Management Tables Migration
-- This creates the core job management tables for the ENABLEDRM platform

-- Create enum types for job management
CREATE TYPE job_type AS ENUM ('command', 'script', 'file_transfer', 'composite');
CREATE TYPE job_status AS ENUM ('draft', 'scheduled', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE execution_status AS ENUM ('scheduled', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE action_type AS ENUM ('command', 'script', 'file_transfer');
CREATE TYPE log_phase AS ENUM ('creation', 'target_selection', 'authentication', 'communication', 'action_execution', 'result_collection', 'completion');
CREATE TYPE log_level AS ENUM ('info', 'warning', 'error', 'debug');
CREATE TYPE log_category AS ENUM ('authentication', 'communication', 'command_execution', 'file_transfer', 'system');

-- Core job entity
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    job_serial VARCHAR(20) UNIQUE NOT NULL DEFAULT 'JOB-' || LPAD(nextval('jobs_id_seq')::text, 6, '0'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    job_type job_type NOT NULL DEFAULT 'command',
    status job_status NOT NULL DEFAULT 'draft',
    created_by INTEGER NOT NULL, -- References user from user-service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Job actions (commands, scripts, etc.)
CREATE TABLE job_actions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action_order INTEGER NOT NULL,
    action_type action_type NOT NULL,
    action_name VARCHAR(255) NOT NULL,
    action_parameters JSONB,
    action_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job target associations (which targets a job can run on)
CREATE TABLE job_targets (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES universal_targets(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, target_id)
);

-- Job executions (when jobs run)
CREATE TABLE job_executions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    execution_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    execution_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'EXEC-' || LPAD(nextval('job_executions_id_seq')::text, 8, '0'),
    execution_number INTEGER NOT NULL,
    status execution_status NOT NULL DEFAULT 'scheduled',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job execution branches (per target)
CREATE TABLE job_execution_branches (
    id SERIAL PRIMARY KEY,
    job_execution_id INTEGER NOT NULL REFERENCES job_executions(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES universal_targets(id),
    branch_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    branch_serial VARCHAR(100) UNIQUE NOT NULL DEFAULT 'BRANCH-' || LPAD(nextval('job_execution_branches_id_seq')::text, 8, '0'),
    branch_id VARCHAR(10) NOT NULL, -- 001, 002, 003, etc.
    target_serial_ref VARCHAR(50),
    status execution_status NOT NULL DEFAULT 'scheduled',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result_output TEXT,
    result_error TEXT,
    exit_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job execution logs
CREATE TABLE job_execution_logs (
    id SERIAL PRIMARY KEY,
    job_execution_id INTEGER REFERENCES job_executions(id) ON DELETE CASCADE,
    branch_id INTEGER REFERENCES job_execution_branches(id) ON DELETE CASCADE,
    log_phase log_phase NOT NULL,
    log_level log_level NOT NULL DEFAULT 'info',
    log_category log_category NOT NULL,
    log_message TEXT NOT NULL,
    log_details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_jobs_created_by ON jobs(created_by);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_scheduled_at ON jobs(scheduled_at);
CREATE INDEX idx_jobs_job_uuid ON jobs(job_uuid);
CREATE INDEX idx_jobs_job_serial ON jobs(job_serial);
CREATE INDEX idx_job_actions_job_id ON job_actions(job_id);
CREATE INDEX idx_job_actions_order ON job_actions(job_id, action_order);
CREATE INDEX idx_job_targets_job_id ON job_targets(job_id);
CREATE INDEX idx_job_targets_target_id ON job_targets(target_id);
CREATE INDEX idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_execution_uuid ON job_executions(execution_uuid);
CREATE INDEX idx_job_executions_execution_serial ON job_executions(execution_serial);
CREATE INDEX idx_job_execution_branches_execution_id ON job_execution_branches(job_execution_id);
CREATE INDEX idx_job_execution_branches_target_id ON job_execution_branches(target_id);
CREATE INDEX idx_job_execution_branches_status ON job_execution_branches(status);
CREATE INDEX idx_job_execution_branches_branch_uuid ON job_execution_branches(branch_uuid);
CREATE INDEX idx_job_execution_branches_branch_serial ON job_execution_branches(branch_serial);
CREATE INDEX idx_job_execution_branches_target_serial_ref ON job_execution_branches(target_serial_ref);
CREATE INDEX idx_job_execution_logs_execution_id ON job_execution_logs(job_execution_id);
CREATE INDEX idx_job_execution_logs_branch_id ON job_execution_logs(branch_id);
CREATE INDEX idx_job_execution_logs_timestamp ON job_execution_logs(timestamp);
CREATE INDEX idx_job_execution_logs_phase ON job_execution_logs(log_phase);
CREATE INDEX idx_job_execution_logs_category ON job_execution_logs(log_category);

-- Add comments for documentation
COMMENT ON TABLE jobs IS 'Core job entity - represents automation jobs';
COMMENT ON TABLE job_actions IS 'Individual actions within jobs (commands, scripts, etc.)';
COMMENT ON TABLE job_targets IS 'Association table linking jobs to their target systems';
COMMENT ON TABLE job_executions IS 'Execution instances of jobs';
COMMENT ON TABLE job_execution_branches IS 'Per-target execution tracking';
COMMENT ON TABLE job_execution_logs IS 'Comprehensive logging with taxonomy-based categorization';
