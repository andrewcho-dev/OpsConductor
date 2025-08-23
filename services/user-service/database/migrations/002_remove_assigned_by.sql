-- Migration: Remove assigned_by column from user_roles table
-- This column was causing SQLAlchemy relationship mapping issues
-- and is not needed for basic role assignment functionality

BEGIN;

-- Drop the foreign key constraint first
ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_assigned_by_fkey;

-- Drop the assigned_by column
ALTER TABLE user_roles DROP COLUMN IF EXISTS assigned_by;

COMMIT;