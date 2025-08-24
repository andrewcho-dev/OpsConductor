-- Discovery System Tables
-- This creates tables for network discovery and device management

-- Discovery Jobs
CREATE TABLE IF NOT EXISTS discovery_jobs (
    id SERIAL PRIMARY KEY,
    discovery_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    discovery_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'DISC-' || LPAD(nextval('discovery_jobs_id_seq')::text, 8, '0'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discovery_type VARCHAR(50) NOT NULL DEFAULT 'network_scan',
    target_range VARCHAR(255) NOT NULL,
    discovery_config JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_by INTEGER NOT NULL, -- References user from user-service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    discovered_count INTEGER DEFAULT 0,
    error_message TEXT
);

-- Discovered Devices
CREATE TABLE IF NOT EXISTS discovered_devices (
    id SERIAL PRIMARY KEY,
    device_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    device_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'DEV-' || LPAD(nextval('discovered_devices_id_seq')::text, 8, '0'),
    discovery_job_id INTEGER NOT NULL REFERENCES discovery_jobs(id) ON DELETE CASCADE,
    ip_address INET NOT NULL,
    hostname VARCHAR(255),
    mac_address VARCHAR(17),
    device_type VARCHAR(100),
    os_type VARCHAR(50),
    os_version VARCHAR(100),
    vendor VARCHAR(100),
    model VARCHAR(100),
    services JSONB,
    ports JSONB,
    is_reachable BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    discovery_method VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Discovery Templates
CREATE TABLE IF NOT EXISTS discovery_templates (
    id SERIAL PRIMARY KEY,
    template_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    template_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'TMPL-' || LPAD(nextval('discovery_templates_id_seq')::text, 8, '0'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discovery_type VARCHAR(50) NOT NULL,
    template_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL, -- References user from user-service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Discovery Schedules
CREATE TABLE IF NOT EXISTS discovery_schedules (
    id SERIAL PRIMARY KEY,
    schedule_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    schedule_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'SCHED-' || LPAD(nextval('discovery_schedules_id_seq')::text, 8, '0'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id INTEGER NOT NULL REFERENCES discovery_templates(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    created_by INTEGER NOT NULL, -- References user from user-service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_discovery_jobs_status ON discovery_jobs(status);
CREATE INDEX IF NOT EXISTS idx_discovery_jobs_created_by ON discovery_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_discovery_jobs_discovery_uuid ON discovery_jobs(discovery_uuid);
CREATE INDEX IF NOT EXISTS idx_discovery_jobs_discovery_serial ON discovery_jobs(discovery_serial);

CREATE INDEX IF NOT EXISTS idx_discovered_devices_discovery_job_id ON discovered_devices(discovery_job_id);
CREATE INDEX IF NOT EXISTS idx_discovered_devices_ip_address ON discovered_devices(ip_address);
CREATE INDEX IF NOT EXISTS idx_discovered_devices_hostname ON discovered_devices(hostname);
CREATE INDEX IF NOT EXISTS idx_discovered_devices_device_type ON discovered_devices(device_type);
CREATE INDEX IF NOT EXISTS idx_discovered_devices_device_uuid ON discovered_devices(device_uuid);
CREATE INDEX IF NOT EXISTS idx_discovered_devices_device_serial ON discovered_devices(device_serial);

CREATE INDEX IF NOT EXISTS idx_discovery_templates_discovery_type ON discovery_templates(discovery_type);
CREATE INDEX IF NOT EXISTS idx_discovery_templates_is_active ON discovery_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_discovery_templates_template_uuid ON discovery_templates(template_uuid);
CREATE INDEX IF NOT EXISTS idx_discovery_templates_template_serial ON discovery_templates(template_serial);

CREATE INDEX IF NOT EXISTS idx_discovery_schedules_template_id ON discovery_schedules(template_id);
CREATE INDEX IF NOT EXISTS idx_discovery_schedules_is_active ON discovery_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_discovery_schedules_next_run ON discovery_schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_discovery_schedules_schedule_uuid ON discovery_schedules(schedule_uuid);
CREATE INDEX IF NOT EXISTS idx_discovery_schedules_schedule_serial ON discovery_schedules(schedule_serial);