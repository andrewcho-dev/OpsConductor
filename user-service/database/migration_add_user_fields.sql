-- Migration: Add missing user fields
-- Date: 2025-08-21
-- Description: Add password_hash, first_name, last_name, phone, department, is_verified, must_change_password, last_login fields

-- Add new columns to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS first_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS department VARCHAR(255),
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_verified ON user_profiles(is_verified);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_login ON user_profiles(last_login);

-- Update existing admin user with default values
UPDATE user_profiles 
SET 
    password_hash = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin123' hashed
    first_name = 'System',
    last_name = 'Administrator',
    is_verified = true,
    must_change_password = false
WHERE user_id = 'admin-user-001';

COMMIT;