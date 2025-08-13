-- =============================================================================
-- REMOVE NAME UNIQUE CONSTRAINT FROM UNIVERSAL TARGETS
-- =============================================================================
-- This migration removes the unique constraint on the name field
-- Multiple targets can now have the same name
-- ONLY constraint should be: No two active targets with same IP address

-- Drop the unique constraint on name field
ALTER TABLE universal_targets DROP CONSTRAINT IF EXISTS ix_universal_targets_name;

-- Drop the unique index on name field  
DROP INDEX IF EXISTS ix_universal_targets_name;

-- Recreate as regular index (not unique)
CREATE INDEX IF NOT EXISTS ix_universal_targets_name ON universal_targets (name);

-- Add comment explaining the constraint policy
COMMENT ON COLUMN universal_targets.name IS 'Target name - NO UNIQUE CONSTRAINT. Multiple targets can have same name. Only IP constraint applies.';