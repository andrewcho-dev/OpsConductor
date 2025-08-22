-- Populate Permanent Identifiers for Existing Records
-- This SQL script populates UUID and serial number fields for existing jobs and targets
-- Run this script if the Python script cannot be executed

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Start transaction
BEGIN;

-- Populate UUIDs for jobs that don't have them
UPDATE jobs 
SET job_uuid = uuid_generate_v4() 
WHERE job_uuid IS NULL;

-- Populate UUIDs for targets that don't have them
UPDATE universal_targets 
SET target_uuid = uuid_generate_v4() 
WHERE target_uuid IS NULL;

-- Populate serial numbers for jobs
DO $$
DECLARE
    job_record RECORD;
    counter INTEGER := 1;
    current_year INTEGER := EXTRACT(YEAR FROM NOW());
    max_existing INTEGER := 0;
BEGIN
    -- Find the highest existing serial number for this year
    SELECT COALESCE(MAX(CAST(SUBSTRING(job_serial FROM 10) AS INTEGER)), 0) 
    INTO max_existing
    FROM jobs 
    WHERE job_serial LIKE 'JOB-' || current_year || '-%';
    
    counter := max_existing + 1;
    
    -- Update jobs that don't have serial numbers
    FOR job_record IN 
        SELECT id FROM jobs 
        WHERE job_serial IS NULL 
        ORDER BY id 
    LOOP
        UPDATE jobs 
        SET job_serial = 'JOB-' || current_year || '-' || LPAD(counter::TEXT, 6, '0')
        WHERE id = job_record.id;
        counter := counter + 1;
    END LOOP;
    
    RAISE NOTICE 'Updated % jobs with serial numbers starting from JOB-%-%.', 
                 counter - max_existing - 1, current_year, LPAD((max_existing + 1)::TEXT, 6, '0');
END $$;

-- Populate serial numbers for targets
DO $$
DECLARE
    target_record RECORD;
    counter INTEGER := 1;
    current_year INTEGER := EXTRACT(YEAR FROM NOW());
    max_existing INTEGER := 0;
BEGIN
    -- Find the highest existing serial number for this year
    SELECT COALESCE(MAX(CAST(SUBSTRING(target_serial FROM 10) AS INTEGER)), 0) 
    INTO max_existing
    FROM universal_targets 
    WHERE target_serial LIKE 'TGT-' || current_year || '-%';
    
    counter := max_existing + 1;
    
    -- Update targets that don't have serial numbers
    FOR target_record IN 
        SELECT id FROM universal_targets 
        WHERE target_serial IS NULL 
        ORDER BY id 
    LOOP
        UPDATE universal_targets 
        SET target_serial = 'TGT-' || current_year || '-' || LPAD(counter::TEXT, 6, '0')
        WHERE id = target_record.id;
        counter := counter + 1;
    END LOOP;
    
    RAISE NOTICE 'Updated % targets with serial numbers starting from TGT-%-%.', 
                 counter - max_existing - 1, current_year, LPAD((max_existing + 1)::TEXT, 6, '0');
END $$;

-- Verify the population
DO $$
DECLARE
    jobs_without_uuid INTEGER;
    jobs_without_serial INTEGER;
    targets_without_uuid INTEGER;
    targets_without_serial INTEGER;
    total_jobs INTEGER;
    total_targets INTEGER;
BEGIN
    -- Count records without identifiers
    SELECT COUNT(*) INTO jobs_without_uuid FROM jobs WHERE job_uuid IS NULL;
    SELECT COUNT(*) INTO jobs_without_serial FROM jobs WHERE job_serial IS NULL;
    SELECT COUNT(*) INTO targets_without_uuid FROM universal_targets WHERE target_uuid IS NULL;
    SELECT COUNT(*) INTO targets_without_serial FROM universal_targets WHERE target_serial IS NULL;
    
    -- Count total records
    SELECT COUNT(*) INTO total_jobs FROM jobs;
    SELECT COUNT(*) INTO total_targets FROM universal_targets;
    
    -- Report results
    RAISE NOTICE '=== POPULATION VERIFICATION ===';
    RAISE NOTICE 'Jobs: % total, % without UUID, % without serial', 
                 total_jobs, jobs_without_uuid, jobs_without_serial;
    RAISE NOTICE 'Targets: % total, % without UUID, % without serial', 
                 total_targets, targets_without_uuid, targets_without_serial;
    
    IF jobs_without_uuid = 0 AND jobs_without_serial = 0 AND 
       targets_without_uuid = 0 AND targets_without_serial = 0 THEN
        RAISE NOTICE '✅ SUCCESS: All records now have permanent identifiers!';
    ELSE
        RAISE NOTICE '❌ WARNING: Some records still missing identifiers';
    END IF;
END $$;

-- Show sample of populated records
SELECT 'JOBS' as table_name, id, job_uuid, job_serial, name 
FROM jobs 
ORDER BY id 
LIMIT 5;

SELECT 'TARGETS' as table_name, id, target_uuid, target_serial, name 
FROM universal_targets 
ORDER BY id 
LIMIT 5;

-- Commit the transaction
COMMIT;

-- Final message
SELECT '🎉 Permanent identifier population completed!' as status;