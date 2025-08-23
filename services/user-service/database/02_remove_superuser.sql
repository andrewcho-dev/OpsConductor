-- Remove is_superuser column from users table
-- This migration removes the superuser concept completely

-- Drop the index first
DROP INDEX IF EXISTS idx_users_is_superuser;

-- Remove the is_superuser column
ALTER TABLE users DROP COLUMN IF EXISTS is_superuser;