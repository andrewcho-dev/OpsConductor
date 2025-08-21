-- Migration: Add soft delete support with deleted_at column
-- Date: 2025-08-21
-- Description: Add deleted_at column to user_profiles table for soft delete functionality

-- Add deleted_at column to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;

-- Create index on deleted_at for performance
CREATE INDEX idx_user_profiles_deleted_at ON user_profiles(deleted_at);

-- Update existing queries to exclude soft-deleted users by default
-- This is handled in the application code, not in the database