-- Notification and Alert Tables
-- This creates tables for notification templates, logs, and alert management

-- Create enum types for notifications
CREATE TYPE notification_type AS ENUM ('email', 'slack', 'webhook', 'sms');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'delivered');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE alert_status AS ENUM ('active', 'acknowledged', 'resolved', 'suppressed');

-- Notification Templates
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    template_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    template_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'NTMPL-' || LPAD(nextval('notification_templates_id_seq')::text, 8, '0'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    notification_type notification_type NOT NULL,
    template_config JSONB NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL, -- References user from user-service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Notification Logs
CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    log_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    log_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'NLOG-' || LPAD(nextval('notification_logs_id_seq')::text, 8, '0'),
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    notification_type notification_type NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    message TEXT NOT NULL,
    status notification_status NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    context_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert Rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    rule_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    rule_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'ARULE-' || LPAD(nextval('alert_rules_id_seq')::text, 8, '0'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(100) NOT NULL,
    condition_config JSONB NOT NULL,
    severity alert_severity NOT NULL DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    notification_template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    cooldown_minutes INTEGER DEFAULT 60,
    created_by INTEGER NOT NULL, -- References user from user-service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Alert Logs
CREATE TABLE IF NOT EXISTS alert_logs (
    id SERIAL PRIMARY KEY,
    alert_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    alert_serial VARCHAR(50) UNIQUE NOT NULL DEFAULT 'ALERT-' || LPAD(nextval('alert_logs_id_seq')::text, 8, '0'),
    alert_rule_id INTEGER NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    severity alert_severity NOT NULL,
    status alert_status NOT NULL DEFAULT 'active',
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by INTEGER, -- References user from user-service
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by INTEGER, -- References user from user-service
    context_data JSONB,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_notification_templates_notification_type ON notification_templates(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_templates_is_active ON notification_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_notification_templates_created_by ON notification_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_notification_templates_template_uuid ON notification_templates(template_uuid);
CREATE INDEX IF NOT EXISTS idx_notification_templates_template_serial ON notification_templates(template_serial);

CREATE INDEX IF NOT EXISTS idx_notification_logs_template_id ON notification_logs(template_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_notification_type ON notification_logs(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_recipient ON notification_logs(recipient);
CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at ON notification_logs(sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_logs_log_uuid ON notification_logs(log_uuid);
CREATE INDEX IF NOT EXISTS idx_notification_logs_log_serial ON notification_logs(log_serial);

CREATE INDEX IF NOT EXISTS idx_alert_rules_rule_type ON alert_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);
CREATE INDEX IF NOT EXISTS idx_alert_rules_is_active ON alert_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_rules_created_by ON alert_rules(created_by);
CREATE INDEX IF NOT EXISTS idx_alert_rules_rule_uuid ON alert_rules(rule_uuid);
CREATE INDEX IF NOT EXISTS idx_alert_rules_rule_serial ON alert_rules(rule_serial);

CREATE INDEX IF NOT EXISTS idx_alert_logs_alert_rule_id ON alert_logs(alert_rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_logs_severity ON alert_logs(severity);
CREATE INDEX IF NOT EXISTS idx_alert_logs_status ON alert_logs(status);
CREATE INDEX IF NOT EXISTS idx_alert_logs_triggered_at ON alert_logs(triggered_at);
CREATE INDEX IF NOT EXISTS idx_alert_logs_acknowledged_by ON alert_logs(acknowledged_by);
CREATE INDEX IF NOT EXISTS idx_alert_logs_resolved_by ON alert_logs(resolved_by);
CREATE INDEX IF NOT EXISTS idx_alert_logs_alert_uuid ON alert_logs(alert_uuid);
CREATE INDEX IF NOT EXISTS idx_alert_logs_alert_serial ON alert_logs(alert_serial);