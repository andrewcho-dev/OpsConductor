-- Targets Service Database Initialization

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS targets_db;
\c targets_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Target types enum
CREATE TYPE target_type AS ENUM ('linux', 'windows', 'network', 'database', 'api', 'container');
CREATE TYPE target_status AS ENUM ('active', 'inactive', 'error', 'pending');
CREATE TYPE connection_method AS ENUM ('ssh', 'winrm', 'http', 'https', 'database', 'custom');

-- Targets table
CREATE TABLE IF NOT EXISTS targets (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    target_type target_type NOT NULL,
    hostname VARCHAR(255),
    ip_address INET,
    port INTEGER,
    connection_method connection_method NOT NULL,
    credentials_id INTEGER, -- Reference to credentials service
    status target_status DEFAULT 'pending',
    tags TEXT[],
    metadata JSONB,
    custom_fields JSONB,
    last_seen TIMESTAMP WITH TIME ZONE,
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(20) DEFAULT 'unknown',
    health_message TEXT,
    discovery_source VARCHAR(100), -- manual, nmap, api, etc.
    environment VARCHAR(50), -- prod, staging, dev, etc.
    organization VARCHAR(200),
    owner_id INTEGER, -- User ID from user service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- Target groups table
CREATE TABLE IF NOT EXISTS target_groups (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- Target group memberships table
CREATE TABLE IF NOT EXISTS target_group_members (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES target_groups(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,
    UNIQUE(target_id, group_id)
);

-- Target credentials table (simplified - full credentials service would be separate)
CREATE TABLE IF NOT EXISTS target_credentials (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    credential_type VARCHAR(50) NOT NULL, -- ssh_key, password, token, etc.
    username VARCHAR(100),
    encrypted_data BYTEA, -- Encrypted credential data
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- Target health checks table
CREATE TABLE IF NOT EXISTS target_health_checks (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL, -- healthy, unhealthy, unknown, timeout
    response_time_ms INTEGER,
    status_code INTEGER,
    message TEXT,
    details JSONB,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Discovery scans table
CREATE TABLE IF NOT EXISTS discovery_scans (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200),
    scan_type VARCHAR(50) NOT NULL, -- nmap, ping_sweep, port_scan, etc.
    ip_ranges TEXT[], -- CIDR ranges to scan
    ports INTEGER[],
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    targets_found INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    config JSONB,
    results JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_targets_hostname ON targets(hostname);
CREATE INDEX IF NOT EXISTS idx_targets_ip ON targets(ip_address);
CREATE INDEX IF NOT EXISTS idx_targets_type ON targets(target_type);
CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status);
CREATE INDEX IF NOT EXISTS idx_targets_uuid ON targets(uuid);
CREATE INDEX IF NOT EXISTS idx_targets_owner ON targets(owner_id);
CREATE INDEX IF NOT EXISTS idx_target_groups_name ON target_groups(name);
CREATE INDEX IF NOT EXISTS idx_target_group_members_target ON target_group_members(target_id);
CREATE INDEX IF NOT EXISTS idx_target_group_members_group ON target_group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_health_checks_target ON target_health_checks(target_id);
CREATE INDEX IF NOT EXISTS idx_health_checks_time ON target_health_checks(checked_at);
CREATE INDEX IF NOT EXISTS idx_discovery_scans_status ON discovery_scans(status);
CREATE INDEX IF NOT EXISTS idx_discovery_scans_time ON discovery_scans(created_at);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_targets_updated_at BEFORE UPDATE ON targets FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_target_groups_updated_at BEFORE UPDATE ON target_groups FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_target_credentials_updated_at BEFORE UPDATE ON target_credentials FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();