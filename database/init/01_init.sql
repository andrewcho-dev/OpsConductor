-- OPSCONDUCTOR Platform Database Initialization
-- This script creates the initial database schema

-- Create universal_targets table
CREATE TABLE IF NOT EXISTS universal_targets (
    id SERIAL PRIMARY KEY,
    target_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    target_serial VARCHAR(20) UNIQUE NOT NULL DEFAULT 'TGT-' || LPAD(nextval('universal_targets_id_seq')::text, 6, '0'),
    name VARCHAR(100) NOT NULL,
    target_type VARCHAR(20) NOT NULL DEFAULT 'system',
    description TEXT,
    os_type VARCHAR(20) NOT NULL,
    environment VARCHAR(20) NOT NULL DEFAULT 'development',
    location VARCHAR(100),
    data_center VARCHAR(100),
    region VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    health_status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create target_credentials table
CREATE TABLE IF NOT EXISTS target_credentials (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES universal_targets(id) ON DELETE CASCADE,
    credential_type VARCHAR(50) NOT NULL,
    credential_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create target_communication_methods table
CREATE TABLE IF NOT EXISTS target_communication_methods (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES universal_targets(id) ON DELETE CASCADE,
    method_type VARCHAR(50) NOT NULL,
    method_config JSONB NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for targets
CREATE INDEX IF NOT EXISTS idx_universal_targets_type ON universal_targets(target_type);
CREATE INDEX IF NOT EXISTS idx_universal_targets_active ON universal_targets(is_active);
CREATE INDEX IF NOT EXISTS idx_universal_targets_target_uuid ON universal_targets(target_uuid);
CREATE INDEX IF NOT EXISTS idx_universal_targets_target_serial ON universal_targets(target_serial);
CREATE INDEX IF NOT EXISTS idx_universal_targets_status ON universal_targets(status);
CREATE INDEX IF NOT EXISTS idx_universal_targets_health_status ON universal_targets(health_status);
CREATE INDEX IF NOT EXISTS idx_universal_targets_environment ON universal_targets(environment);
CREATE INDEX IF NOT EXISTS idx_target_credentials_target_id ON target_credentials(target_id);
CREATE INDEX IF NOT EXISTS idx_target_communication_methods_target_id ON target_communication_methods(target_id);

-- Create system settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('timezone', '"UTC"', 'System timezone configuration'),
('inactivity_timeout_minutes', '60', 'User inactivity timeout in minutes for activity-based sessions'),
('warning_time_minutes', '2', 'Warning time in minutes before session timeout'),
('max_concurrent_jobs', '50', 'Maximum concurrent job executions'),
('log_retention_days', '30', 'How long to keep logs in days')
ON CONFLICT (setting_key) DO NOTHING; 