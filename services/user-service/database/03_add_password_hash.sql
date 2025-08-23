-- Add password_hash column to users table for authentication
-- Migration: 03_add_password_hash.sql

-- Add password_hash column
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);

-- Create index for performance (optional but recommended)
CREATE INDEX idx_users_password_hash ON users(password_hash) WHERE password_hash IS NOT NULL;

-- Add comment
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password for authentication';