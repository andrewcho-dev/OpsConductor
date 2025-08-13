-- Migration to add job_targets table for existing databases
-- This migration adds the missing job_targets table that was not included in the original schema

-- Create job_targets table if it doesn't exist
CREATE TABLE IF NOT EXISTS job_targets (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES universal_targets(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, target_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_targets_job_id ON job_targets(job_id);
CREATE INDEX IF NOT EXISTS idx_job_targets_target_id ON job_targets(target_id);

-- Add comment for documentation
COMMENT ON TABLE job_targets IS 'Association table linking jobs to their target systems';

-- Note: Existing jobs will not have target associations, so they will use all active targets
-- as a fallback until they are updated with specific target associations
