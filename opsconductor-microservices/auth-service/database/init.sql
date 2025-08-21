-- Auth Service Database Initialization
-- This script sets up the initial database structure and data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username);
CREATE INDEX IF NOT EXISTS idx_auth_users_uuid ON auth_users(user_uuid);
CREATE INDEX IF NOT EXISTS idx_auth_users_active ON auth_users(is_active);
CREATE INDEX IF NOT EXISTS idx_auth_users_verified ON auth_users(is_verified);
CREATE INDEX IF NOT EXISTS idx_auth_users_locked ON auth_users(is_locked);
CREATE INDEX IF NOT EXISTS idx_auth_users_created_at ON auth_users(created_at);

CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id);
CREATE INDEX IF NOT EXISTS idx_login_history_email ON login_history(email);
CREATE INDEX IF NOT EXISTS idx_login_history_success ON login_history(success);
CREATE INDEX IF NOT EXISTS idx_login_history_created_at ON login_history(created_at);
CREATE INDEX IF NOT EXISTS idx_login_history_ip_address ON login_history(ip_address);

CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_password_history_created_at ON password_history(created_at);

CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_service_name ON api_keys(service_name);
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_used ON password_reset_tokens(is_used);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token_hash ON email_verification_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_used ON email_verification_tokens(is_used);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires_at ON email_verification_tokens(expires_at);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_auth_users_updated_at BEFORE UPDATE ON auth_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for active sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    us.session_id,
    us.user_id,
    u.email,
    u.username,
    us.ip_address,
    us.user_agent,
    us.expires_at,
    us.last_activity,
    us.created_at
FROM user_sessions us
JOIN auth_users u ON us.user_id = u.id
WHERE us.is_active = true 
  AND us.expires_at > CURRENT_TIMESTAMP
  AND u.is_active = true;

-- Create a view for login statistics
CREATE OR REPLACE VIEW login_stats AS
SELECT 
    u.id as user_id,
    u.email,
    u.username,
    COUNT(lh.id) as total_logins,
    COUNT(CASE WHEN lh.success = true THEN 1 END) as successful_logins,
    COUNT(CASE WHEN lh.success = false THEN 1 END) as failed_attempts,
    MAX(CASE WHEN lh.success = true THEN lh.created_at END) as last_successful_login,
    MAX(CASE WHEN lh.success = false THEN lh.created_at END) as last_failed_attempt
FROM auth_users u
LEFT JOIN login_history lh ON u.id = lh.user_id
GROUP BY u.id, u.email, u.username;

-- Insert default admin user (password: admin123!)
-- Note: In production, this should be removed or changed
INSERT INTO auth_users (
    user_uuid,
    email,
    username,
    password_hash,
    is_active,
    is_verified,
    created_at
) VALUES (
    uuid_generate_v4(),
    'admin@opsconductor.local',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjvQSG', -- admin123!
    true,
    true,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO auth_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO auth_user;