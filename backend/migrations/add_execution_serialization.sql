-- Migration: Add Execution Serialization System
-- Description: Adds UUID and serial fields for hierarchical execution tracking
-- Format: J20250001.0001.0001 (Job.Execution.Target)
-- Date: 2025-01-08

-- Add execution serialization fields to job_executions table
ALTER TABLE job_executions 
ADD COLUMN execution_uuid UUID,
ADD COLUMN execution_serial VARCHAR(50);

-- Add branch serialization fields to job_execution_branches table  
ALTER TABLE job_execution_branches
ADD COLUMN branch_uuid UUID,
ADD COLUMN branch_serial VARCHAR(100),
ADD COLUMN target_serial_ref VARCHAR(50);

-- Create indexes for performance
CREATE INDEX idx_job_executions_uuid ON job_executions(execution_uuid);
CREATE INDEX idx_job_executions_serial ON job_executions(execution_serial);
CREATE INDEX idx_job_execution_branches_uuid ON job_execution_branches(branch_uuid);
CREATE INDEX idx_job_execution_branches_serial ON job_execution_branches(branch_serial);
CREATE INDEX idx_job_execution_branches_target_ref ON job_execution_branches(target_serial_ref);

-- Add unique constraints
ALTER TABLE job_executions ADD CONSTRAINT uk_job_executions_uuid UNIQUE (execution_uuid);
ALTER TABLE job_executions ADD CONSTRAINT uk_job_executions_serial UNIQUE (execution_serial);
ALTER TABLE job_execution_branches ADD CONSTRAINT uk_job_execution_branches_uuid UNIQUE (branch_uuid);
ALTER TABLE job_execution_branches ADD CONSTRAINT uk_job_execution_branches_serial UNIQUE (branch_serial);

-- Comments for documentation
COMMENT ON COLUMN job_executions.execution_uuid IS 'Unique UUID for this execution';
COMMENT ON COLUMN job_executions.execution_serial IS 'Hierarchical serial: J20250001.0001';
COMMENT ON COLUMN job_execution_branches.branch_uuid IS 'Unique UUID for this target execution';
COMMENT ON COLUMN job_execution_branches.branch_serial IS 'Full hierarchical serial: J20250001.0001.0001';
COMMENT ON COLUMN job_execution_branches.target_serial_ref IS 'Reference to target serial (T20250001)';