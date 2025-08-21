-- Universal Targets Service Database Initialization
-- This script sets up the initial database structure and data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_targets_name ON targets(name);
CREATE INDEX IF NOT EXISTS idx_targets_type ON targets(target_type);
CREATE INDEX IF NOT EXISTS idx_targets_os_type ON targets(os_type);
CREATE INDEX IF NOT EXISTS idx_targets_environment ON targets(environment);
CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status);
CREATE INDEX IF NOT EXISTS idx_targets_health_status ON targets(health_status);
CREATE INDEX IF NOT EXISTS idx_targets_active ON targets(is_active);
CREATE INDEX IF NOT EXISTS idx_targets_created_at ON targets(created_at);

CREATE INDEX IF NOT EXISTS idx_connection_methods_target_id ON connection_methods(target_id);
CREATE INDEX IF NOT EXISTS idx_connection_methods_type ON connection_methods(method_type);
CREATE INDEX IF NOT EXISTS idx_connection_methods_primary ON connection_methods(is_primary);
CREATE INDEX IF NOT EXISTS idx_connection_methods_active ON connection_methods(is_active);

CREATE INDEX IF NOT EXISTS idx_credentials_method_id ON credentials(connection_method_id);
CREATE INDEX IF NOT EXISTS idx_credentials_type ON credentials(credential_type);
CREATE INDEX IF NOT EXISTS idx_credentials_primary ON credentials(is_primary);
CREATE INDEX IF NOT EXISTS idx_credentials_active ON credentials(is_active);

CREATE INDEX IF NOT EXISTS idx_health_checks_target_id ON target_health_checks(target_id);
CREATE INDEX IF NOT EXISTS idx_health_checks_checked_at ON target_health_checks(checked_at);
CREATE INDEX IF NOT EXISTS idx_health_checks_status ON target_health_checks(status);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_targets_tags_gin ON targets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_targets_metadata_gin ON targets USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_connection_methods_config_gin ON connection_methods USING GIN(config);
CREATE INDEX IF NOT EXISTS idx_health_checks_details_gin ON target_health_checks USING GIN(details);

-- Insert default data (if needed)
-- This could include default target types, method types, etc.

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_targets_updated_at BEFORE UPDATE ON targets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_connection_methods_updated_at BEFORE UPDATE ON connection_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_credentials_updated_at BEFORE UPDATE ON credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for target summaries (for better performance)
CREATE OR REPLACE VIEW target_summaries AS
SELECT 
    t.id,
    t.target_uuid,
    t.target_serial,
    t.name,
    t.target_type,
    t.os_type,
    t.environment,
    t.status,
    t.health_status,
    t.is_active,
    t.created_at,
    t.updated_at,
    cm.config->>'host' as primary_host,
    cm.method_type as primary_method_type
FROM targets t
LEFT JOIN connection_methods cm ON t.id = cm.target_id AND cm.is_primary = true AND cm.is_active = true
WHERE t.is_active = true;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO targets_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO targets_user;