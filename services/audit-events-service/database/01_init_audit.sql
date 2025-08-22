-- Audit Events Service Database Initialization

-- Note: Database is already created by POSTGRES_DB environment variable
-- So we just connect to it and set up the schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Event severity enum
CREATE TYPE event_severity AS ENUM ('info', 'warning', 'error', 'critical');
CREATE TYPE event_category AS ENUM (
    'authentication', 'authorization', 'user_management', 'target_management', 
    'job_management', 'job_execution', 'system', 'configuration', 'security'
);

-- Audit events table
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    category event_category NOT NULL,
    severity event_severity DEFAULT 'info',
    message TEXT NOT NULL,
    description TEXT,
    user_id INTEGER, -- User who performed the action
    username VARCHAR(100),
    user_ip INET,
    user_agent TEXT,
    resource_type VARCHAR(50), -- What was affected (user, target, job, etc.)
    resource_id INTEGER, -- ID of the affected resource
    resource_name VARCHAR(200), -- Name of the affected resource
    action VARCHAR(50) NOT NULL, -- create, update, delete, execute, etc.
    old_values JSONB, -- Previous values (for updates)
    new_values JSONB, -- New values (for creates/updates)
    metadata JSONB, -- Additional context data
    session_id VARCHAR(100), -- User session ID
    request_id VARCHAR(100), -- Request correlation ID
    service_name VARCHAR(50), -- Which service generated the event
    source_ip INET, -- Source IP (may differ from user_ip in proxy scenarios)
    outcome VARCHAR(20) DEFAULT 'success', -- success, failure, partial
    error_code VARCHAR(20),
    error_message TEXT,
    duration_ms INTEGER, -- How long the action took
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- When the actual event occurred
);

-- Security events table (subset of audit events with additional fields)
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    audit_event_id INTEGER REFERENCES audit_events(id) ON DELETE CASCADE,
    threat_level INTEGER DEFAULT 1, -- 1-10 scale
    detection_method VARCHAR(50), -- rule_based, anomaly_detection, manual, etc.
    indicators JSONB, -- IOCs, patterns, etc.
    false_positive BOOLEAN DEFAULT FALSE,
    investigation_status VARCHAR(20) DEFAULT 'new', -- new, investigating, resolved, dismissed
    assigned_to INTEGER, -- User ID of investigator
    investigation_notes TEXT,
    remediation_actions JSONB,
    resolution VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit trails table (for tracking changes to specific resources)
CREATE TABLE IF NOT EXISTS audit_trails (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER NOT NULL,
    resource_uuid UUID,
    version INTEGER DEFAULT 1,
    change_type VARCHAR(20) NOT NULL, -- create, update, delete, restore
    field_changes JSONB, -- Specific field changes
    full_record JSONB, -- Complete record snapshot
    changed_by INTEGER, -- User ID
    change_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX(resource_type, resource_id),
    INDEX(resource_uuid),
    INDEX(changed_by),
    INDEX(created_at)
);

-- Event aggregations table (for reporting and analytics)
CREATE TABLE IF NOT EXISTS event_aggregations (
    id SERIAL PRIMARY KEY,
    aggregation_type VARCHAR(50) NOT NULL, -- hourly, daily, weekly, monthly
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(100),
    category event_category,
    severity event_severity,
    user_id INTEGER,
    service_name VARCHAR(50),
    outcome VARCHAR(20),
    event_count INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(aggregation_type, time_bucket, event_type, category, severity, user_id, service_name, outcome)
);

-- Compliance reports table
CREATE TABLE IF NOT EXISTS compliance_reports (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- sox, pci_dss, hipaa, gdpr, etc.
    title VARCHAR(200) NOT NULL,
    description TEXT,
    date_range_start TIMESTAMP WITH TIME ZONE NOT NULL,
    date_range_end TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- draft, generated, approved, published
    criteria JSONB, -- Report criteria/filters
    findings JSONB, -- Report findings
    recommendations TEXT,
    generated_by INTEGER, -- User ID
    approved_by INTEGER, -- User ID
    file_path TEXT, -- Path to generated report file
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data retention policies table
CREATE TABLE IF NOT EXISTS retention_policies (
    id SERIAL PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    table_name VARCHAR(50) NOT NULL,
    retention_days INTEGER NOT NULL,
    archive_before_delete BOOLEAN DEFAULT TRUE,
    archive_location TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_cleanup_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_category ON audit_events(category);
CREATE INDEX IF NOT EXISTS idx_audit_events_severity ON audit_events(severity);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_audit_events_outcome ON audit_events(outcome);
CREATE INDEX IF NOT EXISTS idx_audit_events_service ON audit_events(service_name);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at ON audit_events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_uuid ON audit_events(uuid);
CREATE INDEX IF NOT EXISTS idx_audit_events_session ON audit_events(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_request ON audit_events(request_id);

CREATE INDEX IF NOT EXISTS idx_security_events_threat_level ON security_events(threat_level);
CREATE INDEX IF NOT EXISTS idx_security_events_status ON security_events(investigation_status);
CREATE INDEX IF NOT EXISTS idx_security_events_assigned ON security_events(assigned_to);
CREATE INDEX IF NOT EXISTS idx_security_events_false_positive ON security_events(false_positive);

CREATE INDEX IF NOT EXISTS idx_audit_trails_resource ON audit_trails(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_trails_uuid ON audit_trails(resource_uuid);
CREATE INDEX IF NOT EXISTS idx_audit_trails_changed_by ON audit_trails(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_trails_created_at ON audit_trails(created_at);

CREATE INDEX IF NOT EXISTS idx_event_aggregations_bucket ON event_aggregations(aggregation_type, time_bucket);
CREATE INDEX IF NOT EXISTS idx_event_aggregations_type ON event_aggregations(event_type);

CREATE INDEX IF NOT EXISTS idx_compliance_reports_type ON compliance_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_status ON compliance_reports(status);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_date_range ON compliance_reports(date_range_start, date_range_end);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_event_aggregations_updated_at BEFORE UPDATE ON event_aggregations FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_compliance_reports_updated_at BEFORE UPDATE ON compliance_reports FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_retention_policies_updated_at BEFORE UPDATE ON retention_policies FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Create default retention policies
INSERT INTO retention_policies (policy_name, description, table_name, retention_days) VALUES
    ('audit_events_default', 'Default retention for audit events', 'audit_events', 2555), -- 7 years
    ('security_events_extended', 'Extended retention for security events', 'security_events', 3650), -- 10 years
    ('audit_trails_default', 'Default retention for audit trails', 'audit_trails', 2555), -- 7 years
    ('event_aggregations_default', 'Default retention for aggregated events', 'event_aggregations', 1095) -- 3 years
ON CONFLICT (policy_name) DO NOTHING;