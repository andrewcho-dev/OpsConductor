-- Add action_serial column to job_action_results table
-- Migration: Add action-level serialization for complete hierarchy

-- Add the action_serial column
ALTER TABLE job_action_results 
ADD COLUMN action_serial VARCHAR(100);

-- Create index for performance
CREATE INDEX idx_job_action_results_action_serial ON job_action_results(action_serial);

-- Add unique constraint (will be populated by script first)
-- ALTER TABLE job_action_results ADD CONSTRAINT uq_job_action_results_action_serial UNIQUE (action_serial);

-- Note: The unique constraint will be added after populating existing records
-- Run populate_action_serials.py script after this migration