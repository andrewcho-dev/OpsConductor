-- Auth Service Database Initialization
-- Comprehensive database schema for authentication and user management

-- Create enhanced users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    
    -- Account status and security
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    must_change_password BOOLEAN DEFAULT FALSE,
    
    -- Password management
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    password_expires_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- Activity tracking
    last_login TIMESTAMP WITH TIME ZONE,
    last_login_ip VARCHAR(45),
    last_password_change TIMESTAMP WITH TIME ZONE,
    
    -- Profile information
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    department VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_locked ON users(is_locked);
CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified);
CREATE INDEX IF NOT EXISTS idx_users_must_change_password ON users(must_change_password);
CREATE INDEX IF NOT EXISTS idx_users_password_expires_at ON users(password_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);

-- Create enhanced user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Session metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    
    -- Session timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Session status
    is_active BOOLEAN DEFAULT TRUE,
    logout_reason VARCHAR(50)
);

-- Create indexes for user_sessions table
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);

-- Create password_history table
CREATE TABLE IF NOT EXISTS password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for password_history table
CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_password_history_created_at ON password_history(created_at);

-- Create user_audit_logs table
CREATE TABLE IF NOT EXISTS user_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT,
    
    -- Context information
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Additional data
    metadata JSONB,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user_audit_logs table
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON user_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON user_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON user_audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address ON user_audit_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_audit_logs_metadata ON user_audit_logs USING GIN(metadata);

-- Create auth_configuration table
CREATE TABLE IF NOT EXISTS auth_configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by INTEGER
);

-- Create indexes for auth_configuration table
CREATE INDEX IF NOT EXISTS idx_auth_config_key ON auth_configuration(config_key);
CREATE INDEX IF NOT EXISTS idx_auth_config_category ON auth_configuration(category);
CREATE INDEX IF NOT EXISTS idx_auth_config_type ON auth_configuration(config_type);

-- Insert default configuration values
INSERT INTO auth_configuration (config_key, config_value, config_type, description, category) VALUES
-- Session Management
('session.timeout_minutes', '30', 'integer', 'Session timeout in minutes', 'session'),
('session.warning_minutes', '5', 'integer', 'Minutes before session timeout to show warning', 'session'),
('session.max_concurrent', '3', 'integer', 'Maximum concurrent sessions per user', 'session'),
('session.idle_timeout_minutes', '15', 'integer', 'Idle timeout in minutes', 'session'),
('session.remember_me_days', '30', 'integer', 'Remember me duration in days', 'session'),

-- Password Policies
('password.min_length', '8', 'integer', 'Minimum password length', 'password'),
('password.max_length', '128', 'integer', 'Maximum password length', 'password'),
('password.require_uppercase', 'true', 'boolean', 'Require at least one uppercase letter', 'password'),
('password.require_lowercase', 'true', 'boolean', 'Require at least one lowercase letter', 'password'),
('password.require_numbers', 'true', 'boolean', 'Require at least one number', 'password'),
('password.require_special', 'true', 'boolean', 'Require at least one special character', 'password'),
('password.special_chars', '!@#$%^&*()_+-=[]{}|;:,.<>?', 'string', 'Allowed special characters', 'password'),
('password.expiry_days', '90', 'integer', 'Password expiry in days (0 = never expires)', 'password'),
('password.history_count', '5', 'integer', 'Number of previous passwords to remember', 'password'),
('password.min_age_hours', '24', 'integer', 'Minimum hours before password can be changed again', 'password'),

-- Account Security
('security.max_failed_attempts', '5', 'integer', 'Maximum failed login attempts before lockout', 'security'),
('security.lockout_duration_minutes', '30', 'integer', 'Account lockout duration in minutes', 'security'),
('security.progressive_lockout', 'true', 'boolean', 'Enable progressive lockout (longer lockouts for repeated failures)', 'security'),
('security.require_email_verification', 'true', 'boolean', 'Require email verification for new accounts', 'security'),
('security.force_password_change_first_login', 'true', 'boolean', 'Force password change on first login', 'security'),
('security.enable_two_factor', 'false', 'boolean', 'Enable two-factor authentication', 'security'),

-- Audit and Compliance
('audit.log_all_events', 'true', 'boolean', 'Log all authentication events', 'audit'),
('audit.retention_days', '365', 'integer', 'Audit log retention period in days', 'audit'),
('audit.log_failed_attempts', 'true', 'boolean', 'Log failed login attempts', 'audit'),

-- User Management
('users.default_role', 'user', 'string', 'Default role for new users', 'users'),
('users.allow_self_registration', 'false', 'boolean', 'Allow users to self-register', 'users'),
('users.require_admin_approval', 'true', 'boolean', 'Require admin approval for new accounts', 'users')

ON CONFLICT (config_key) DO NOTHING;

-- Create default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role, is_active, is_verified, must_change_password)
VALUES (
    'admin',
    'admin@opsconductor.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e', -- admin123
    'administrator',
    TRUE,
    TRUE,
    FALSE
) ON CONFLICT (username) DO NOTHING;

-- Create default user (password: user123)
INSERT INTO users (username, email, password_hash, role, is_active, is_verified, must_change_password)
VALUES (
    'user',
    'user@opsconductor.local',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- user123
    'user',
    TRUE,
    TRUE,
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- Create a test manager user (password: manager123)
INSERT INTO users (username, email, password_hash, role, is_active, is_verified, must_change_password, first_name, last_name, department)
VALUES (
    'manager',
    'manager@opsconductor.local',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- manager123
    'manager',
    TRUE,
    TRUE,
    FALSE,
    'Test',
    'Manager',
    'Operations'
) ON CONFLICT (username) DO NOTHING;