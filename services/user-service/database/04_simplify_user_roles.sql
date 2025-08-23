-- Migration: Simplify user-role relationship
-- Drop the complex many-to-many user_roles table and add simple role_id foreign key

-- Add role_id column to users table
ALTER TABLE users ADD COLUMN role_id INTEGER;

-- Add foreign key constraint
ALTER TABLE users ADD CONSTRAINT fk_users_role_id 
    FOREIGN KEY (role_id) REFERENCES roles(id);

-- Create index for performance
CREATE INDEX idx_users_role_id ON users(role_id);

-- Drop the old user_roles table (if it exists)
DROP TABLE IF EXISTS user_roles;

-- Update any existing users to have a default role (we'll set this after roles are created)
-- This will be handled by the seeding script