-- Migration: Add Permanent Identifiers to Jobs and Targets
-- This migration adds UUID and serial number fields for complete historical traceability

-- Add UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Add permanent identifier columns to jobs table
ALTER TABLE jobs 
ADD COLUMN job_uuid UUID UNIQUE DEFAULT uuid_generate_v4(),
ADD COLUMN job_serial VARCHAR(20) UNIQUE;

-- Add permanent identifier columns to universal_targets table  
ALTER TABLE universal_targets
ADD COLUMN target_uuid UUID UNIQUE DEFAULT uuid_generate_v4(),
ADD COLUMN target_serial VARCHAR(20) UNIQUE;

-- Create indexes for performance
CREATE INDEX idx_jobs_job_uuid ON jobs(job_uuid);
CREATE INDEX idx_jobs_job_serial ON jobs(job_serial);
CREATE INDEX idx_targets_target_uuid ON universal_targets(target_uuid);
CREATE INDEX idx_targets_target_serial ON universal_targets(target_serial);

-- Generate serial numbers for existing jobs
DO $$
DECLARE
    job_record RECORD;
    counter INTEGER := 1;
    current_year INTEGER := EXTRACT(YEAR FROM NOW());
BEGIN
    FOR job_record IN SELECT id FROM jobs ORDER BY id LOOP
        UPDATE jobs 
        SET job_serial = 'JOB-' || current_year || '-' || LPAD(counter::TEXT, 6, '0')
        WHERE id = job_record.id;
        counter := counter + 1;
    END LOOP;
END $$;

-- Generate serial numbers for existing targets
DO $$
DECLARE
    target_record RECORD;
    counter INTEGER := 1;
    current_year INTEGER := EXTRACT(YEAR FROM NOW());
BEGIN
    FOR target_record IN SELECT id FROM universal_targets ORDER BY id LOOP
        UPDATE universal_targets 
        SET target_serial = 'TGT-' || current_year || '-' || LPAD(counter::TEXT, 6, '0')
        WHERE id = target_record.id;
        counter := counter + 1;
    END LOOP;
END $$;

-- Make the new columns NOT NULL after populating them
ALTER TABLE jobs 
ALTER COLUMN job_uuid SET NOT NULL,
ALTER COLUMN job_serial SET NOT NULL;

ALTER TABLE universal_targets
ALTER COLUMN target_uuid SET NOT NULL,
ALTER COLUMN target_serial SET NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN jobs.job_uuid IS 'Permanent, immutable UUID for historical traceability';
COMMENT ON COLUMN jobs.job_serial IS 'Human-readable permanent identifier: JOB-YYYY-NNNNNN';
COMMENT ON COLUMN universal_targets.target_uuid IS 'Permanent, immutable UUID for historical traceability';
COMMENT ON COLUMN universal_targets.target_serial IS 'Human-readable permanent identifier: TGT-YYYY-NNNNNN';