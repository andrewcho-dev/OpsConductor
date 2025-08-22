-- Auth Service Database Initialization

-- Note: Database is already created by POSTGRES_DB environment variable
-- So we just connect to it and set up the schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Auth-related enums
CREATE TYPE session_status AS ENUM ('active', 'expired', 'revoked', 'logged_out');
CREATE TYPE token_type AS ENUM ('access', 'refresh', 'reset_password', 'email_verification', 'api_key');
CREATE TYPE token_status AS ENUM ('active', 'expired', 'revoked', 'used');
CREATE TYPE login_status AS ENUM ('success', 'failed', 'blocked', 'suspicious');
CREATE TYPE oauth_provider AS ENUM ('google', 'microsoft', 'github', 'okta', 'custom');

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER NOT NULL, -- Reference to user service
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    status session_status DEFAULT 'active',
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    location JSONB, -- Geolocation data
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by INTEGER, -- User ID who revoked (admin or self)
    revocation_reason VARCHAR(100),
    metadata JSONB
);

-- JWT token blacklist table (for invalidated tokens)
CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    token_id VARCHAR(255) NOT NULL, -- JWT 'jti' claim
    token_type token_type NOT NULL,
    user_id INTEGER, -- User the token belonged to
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    blacklisted_by INTEGER, -- User who blacklisted it
    reason VARCHAR(200),
    metadata JSONB
);

-- Refresh tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed refresh token
    user_id INTEGER NOT NULL,
    session_id INTEGER REFERENCES user_sessions(id) ON DELETE CASCADE,
    status token_status DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    use_count INTEGER DEFAULT 0,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(200)
);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed token
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Email verification tokens table
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OAuth providers table
CREATE TABLE IF NOT EXISTS oauth_providers (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type oauth_provider NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    client_secret_encrypted BYTEA, -- Encrypted client secret
    authorization_url VARCHAR(500),
    token_url VARCHAR(500),
    user_info_url VARCHAR(500),
    scope VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB, -- Provider-specific configuration
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OAuth user connections table
CREATE TABLE IF NOT EXISTS oauth_user_connections (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL REFERENCES oauth_providers(id) ON DELETE CASCADE,
    provider_user_id VARCHAR(255) NOT NULL, -- ID from OAuth provider
    provider_username VARCHAR(255),
    provider_email VARCHAR(255),
    access_token_encrypted BYTEA, -- Encrypted OAuth access token
    refresh_token_encrypted BYTEA, -- Encrypted OAuth refresh token
    token_expires_at TIMESTAMP WITH TIME ZONE,
    profile_data JSONB, -- User profile from OAuth provider
    is_primary BOOLEAN DEFAULT FALSE, -- Primary OAuth connection for user
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, provider_user_id),
    UNIQUE(user_id, provider_id) -- One connection per user per provider
);

-- API keys table (for service-to-service authentication)
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed API key
    key_prefix VARCHAR(20) NOT NULL, -- First few characters for identification
    user_id INTEGER, -- User who created the key
    service_name VARCHAR(100), -- Service this key belongs to
    permissions TEXT[], -- Array of permissions
    ip_whitelist INET[], -- Allowed IP addresses
    rate_limit_per_hour INTEGER DEFAULT 1000,
    rate_limit_per_day INTEGER DEFAULT 10000,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    use_count INTEGER DEFAULT 0,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by INTEGER,
    revocation_reason VARCHAR(200)
);

-- Login attempts table (for security monitoring)
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER, -- NULL if user not found
    email VARCHAR(255),
    username VARCHAR(255),
    status login_status NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255), -- Browser/device fingerprint
    location JSONB, -- Geolocation data
    failure_reason VARCHAR(200), -- Why login failed
    session_id INTEGER REFERENCES user_sessions(id),
    oauth_provider_id INTEGER REFERENCES oauth_providers(id),
    is_suspicious BOOLEAN DEFAULT FALSE,
    risk_score INTEGER DEFAULT 0, -- 0-100 risk assessment
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Auth audit log table
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- login, logout, token_refresh, password_change, etc.
    user_id INTEGER,
    session_id INTEGER REFERENCES user_sessions(id),
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20) NOT NULL, -- success, failure, blocked
    details JSONB, -- Event-specific details
    security_flags TEXT[], -- suspicious_ip, multiple_failures, etc.
    request_id VARCHAR(100), -- Correlation ID
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rate limiting table
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL, -- IP, user_id, api_key, etc.
    limit_type VARCHAR(50) NOT NULL, -- login_attempts, api_calls, etc.
    count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB,
    UNIQUE(identifier, limit_type, window_start)
);

-- Security policies table
CREATE TABLE IF NOT EXISTS security_policies (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    policy_type VARCHAR(50) NOT NULL, -- password, session, mfa, etc.
    rules JSONB NOT NULL, -- Policy rules configuration
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    applies_to TEXT[], -- user roles, specific users, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_status ON user_sessions(status);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_activity ON user_sessions(last_activity);

CREATE INDEX IF NOT EXISTS idx_token_blacklist_token_id ON token_blacklist(token_id);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_user ON token_blacklist(user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_session ON refresh_tokens(session_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_password_reset_hash ON password_reset_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_email_verification_hash ON email_verification_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_email_verification_user ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_expires ON email_verification_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_oauth_connections_user ON oauth_user_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_connections_provider ON oauth_user_connections(provider_id);
CREATE INDEX IF NOT EXISTS idx_oauth_connections_provider_user ON oauth_user_connections(provider_user_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service_name);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_status ON login_attempts(status);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_suspicious ON login_attempts(is_suspicious);

CREATE INDEX IF NOT EXISTS idx_auth_audit_user ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_event ON auth_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_audit_time ON auth_audit_log(occurred_at);
CREATE INDEX IF NOT EXISTS idx_auth_audit_session ON auth_audit_log(session_id);

CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier);
CREATE INDEX IF NOT EXISTS idx_rate_limits_type ON rate_limits(limit_type);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_end);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_oauth_providers_updated_at BEFORE UPDATE ON oauth_providers FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_oauth_connections_updated_at BEFORE UPDATE ON oauth_user_connections FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_security_policies_updated_at BEFORE UPDATE ON security_policies FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Insert default security policies
INSERT INTO security_policies (name, description, policy_type, rules, is_default) VALUES
(
    'Default Session Policy', 
    'Default session management policy',
    'session',
    '{
        "max_session_duration_hours": 8,
        "idle_timeout_minutes": 30,
        "max_concurrent_sessions": 5,
        "require_fresh_login_for_sensitive_ops": true,
        "session_fixation_protection": true
    }'::jsonb,
    true
),
(
    'Default Password Policy',
    'Default password requirements policy', 
    'password',
    '{
        "min_length": 8,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_numbers": true,
        "require_special_chars": true,
        "prevent_password_reuse": 5,
        "password_expiry_days": 90,
        "failed_attempts_lockout": 5,
        "lockout_duration_minutes": 15
    }'::jsonb,
    true
),
(
    'Default Rate Limiting Policy',
    'Default API and login rate limiting',
    'rate_limiting', 
    '{
        "login_attempts_per_ip_per_hour": 20,
        "login_attempts_per_user_per_hour": 10,
        "api_calls_per_key_per_hour": 1000,
        "api_calls_per_ip_per_hour": 5000,
        "password_reset_per_email_per_hour": 3
    }'::jsonb,
    true
)
ON CONFLICT (name) DO NOTHING;

-- Insert default OAuth providers (disabled by default)
INSERT INTO oauth_providers (name, provider_type, client_id, authorization_url, token_url, user_info_url, scope, is_active) VALUES
(
    'Google OAuth',
    'google',
    'your-google-client-id',
    'https://accounts.google.com/o/oauth2/v2/auth',
    'https://oauth2.googleapis.com/token',
    'https://www.googleapis.com/oauth2/v2/userinfo',
    'openid email profile',
    false
),
(
    'Microsoft OAuth',
    'microsoft', 
    'your-microsoft-client-id',
    'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    'https://graph.microsoft.com/v1.0/me',
    'openid email profile',
    false
),
(
    'GitHub OAuth',
    'github',
    'your-github-client-id', 
    'https://github.com/login/oauth/authorize',
    'https://github.com/login/oauth/access_token',
    'https://api.github.com/user',
    'user:email',
    false
)
ON CONFLICT (name) DO NOTHING;

-- Clean up expired tokens and sessions (this would typically be run by a scheduled job)
-- This is just a placeholder for the cleanup logic
CREATE OR REPLACE FUNCTION cleanup_expired_auth_data()
RETURNS void AS $$
BEGIN
    -- Delete expired password reset tokens
    DELETE FROM password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Delete expired email verification tokens  
    DELETE FROM email_verification_tokens WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Delete expired blacklisted tokens
    DELETE FROM token_blacklist WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Delete old rate limit entries (older than 24 hours)
    DELETE FROM rate_limits WHERE window_end < CURRENT_TIMESTAMP - INTERVAL '24 hours';
    
    -- Delete old login attempts (older than 30 days)
    DELETE FROM login_attempts WHERE attempted_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Delete old auth audit log entries (older than 1 year)
    DELETE FROM auth_audit_log WHERE occurred_at < CURRENT_TIMESTAMP - INTERVAL '1 year';
END;
$$ LANGUAGE plpgsql;