-- Notifications Service Database Initialization

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS notification_db;
\c notification_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Notification types and status enums
CREATE TYPE notification_type AS ENUM (
    'email', 'sms', 'push', 'webhook', 'slack', 'teams', 'discord', 'custom'
);
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'cancelled');
CREATE TYPE notification_priority AS ENUM ('low', 'normal', 'high', 'urgent');
CREATE TYPE template_type AS ENUM ('email', 'sms', 'push', 'webhook', 'generic');

-- Notification templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    template_type template_type NOT NULL,
    subject_template TEXT, -- For email/push notifications
    body_template TEXT NOT NULL, -- Template with placeholders
    html_template TEXT, -- HTML version for emails
    variables JSONB, -- Available variables and their descriptions
    default_values JSONB, -- Default values for variables
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE, -- System templates can't be deleted
    category VARCHAR(100), -- job_completion, system_alert, user_action, etc.
    tags TEXT[],
    created_by INTEGER, -- User ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification channels table (where to send notifications)
CREATE TABLE IF NOT EXISTS notification_channels (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    channel_type notification_type NOT NULL,
    configuration JSONB NOT NULL, -- Channel-specific config (SMTP, webhook URL, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE, -- Default channel for this type
    rate_limit_per_hour INTEGER, -- Rate limiting
    rate_limit_per_day INTEGER,
    last_used_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User notification preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL, -- Reference to user service
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    email_address VARCHAR(255),
    phone_number VARCHAR(20),
    push_token TEXT, -- For mobile push notifications
    timezone VARCHAR(50) DEFAULT 'UTC',
    quiet_hours_start TIME, -- Don't send notifications during these hours
    quiet_hours_end TIME,
    preferred_channels JSONB, -- Channel preferences per notification type
    frequency_limits JSONB, -- How often to receive certain types
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Notification rules table (when to send notifications)
CREATE TABLE IF NOT EXISTS notification_rules (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(100) NOT NULL, -- job_completed, job_failed, user_created, etc.
    conditions JSONB, -- Conditions that must be met to trigger
    template_id INTEGER REFERENCES notification_templates(id),
    channels INTEGER[], -- Array of channel IDs to use
    recipients JSONB, -- Who should receive (users, groups, roles)
    priority notification_priority DEFAULT 'normal',
    is_active BOOLEAN DEFAULT TRUE,
    send_to_creator BOOLEAN DEFAULT TRUE, -- Send to person who triggered the event
    send_to_assignee BOOLEAN DEFAULT FALSE, -- Send to assignee if applicable
    cooldown_minutes INTEGER DEFAULT 0, -- Minimum time between same notifications
    max_per_hour INTEGER, -- Rate limiting per rule
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table (actual notification instances)
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    rule_id INTEGER REFERENCES notification_rules(id) ON DELETE SET NULL,
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    channel_id INTEGER REFERENCES notification_channels(id) ON DELETE SET NULL,
    notification_type notification_type NOT NULL,
    status notification_status DEFAULT 'pending',
    priority notification_priority DEFAULT 'normal',
    recipient_user_id INTEGER, -- Specific user recipient
    recipient_email VARCHAR(255), -- Email recipient (may be external)
    recipient_phone VARCHAR(20), -- Phone recipient
    recipient_address TEXT, -- Generic recipient address
    subject TEXT,
    message TEXT NOT NULL,
    html_message TEXT,
    variables JSONB, -- Variable values used in template
    metadata JSONB, -- Additional context data
    event_id VARCHAR(100), -- ID of the event that triggered this
    event_type VARCHAR(100), -- Type of event
    resource_id INTEGER, -- ID of related resource
    resource_type VARCHAR(50), -- Type of related resource
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE, -- If read receipts are supported
    failed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    external_id VARCHAR(200), -- ID from external service (email provider, etc.)
    response_data JSONB, -- Response from external service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification attachments table
CREATE TABLE IF NOT EXISTS notification_attachments (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT, -- Path to stored file
    file_size BIGINT,
    mime_type VARCHAR(100),
    content_data BYTEA, -- For small attachments stored in DB
    is_inline BOOLEAN DEFAULT FALSE, -- For inline images in HTML emails
    content_id VARCHAR(100), -- For referencing in HTML
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification delivery tracking
CREATE TABLE IF NOT EXISTS delivery_tracking (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- queued, sent, delivered, bounced, complained, etc.
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    external_event_id VARCHAR(200), -- ID from external service
    details JSONB, -- Additional event details
    user_agent TEXT, -- For web-based events (email opens, clicks)
    ip_address INET, -- For web-based events
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification statistics (aggregated data)
CREATE TABLE IF NOT EXISTS notification_statistics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    channel_id INTEGER REFERENCES notification_channels(id) ON DELETE CASCADE,
    notification_type notification_type,
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    total_bounced INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0, -- For emails
    total_clicked INTEGER DEFAULT 0, -- For emails with links
    average_delivery_time_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, channel_id, notification_type)
);

-- Webhook subscriptions (for external systems to receive notifications)
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    webhook_url TEXT NOT NULL,
    secret_key VARCHAR(100), -- For HMAC verification
    event_types TEXT[], -- Which event types to send
    is_active BOOLEAN DEFAULT TRUE,
    retry_config JSONB, -- Retry configuration
    headers JSONB, -- Custom headers to include
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_notification_templates_type ON notification_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_notification_templates_active ON notification_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_notification_templates_category ON notification_templates(category);

CREATE INDEX IF NOT EXISTS idx_notification_channels_type ON notification_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_notification_channels_active ON notification_channels(is_active);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_notification_preferences(user_id);

CREATE INDEX IF NOT EXISTS idx_notification_rules_event_type ON notification_rules(event_type);
CREATE INDEX IF NOT EXISTS idx_notification_rules_active ON notification_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient_user ON notifications(recipient_user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_for ON notifications(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_notifications_event ON notifications(event_type, event_id);
CREATE INDEX IF NOT EXISTS idx_notifications_resource ON notifications(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_notifications_uuid ON notifications(uuid);

CREATE INDEX IF NOT EXISTS idx_notification_attachments_notification_id ON notification_attachments(notification_id);

CREATE INDEX IF NOT EXISTS idx_delivery_tracking_notification_id ON delivery_tracking(notification_id);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_event_type ON delivery_tracking(event_type);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_timestamp ON delivery_tracking(event_timestamp);

CREATE INDEX IF NOT EXISTS idx_notification_statistics_date ON notification_statistics(date);
CREATE INDEX IF NOT EXISTS idx_notification_statistics_channel ON notification_statistics(channel_id);

CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_active ON webhook_subscriptions(is_active);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_notification_channels_updated_at BEFORE UPDATE ON notification_channels FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_user_notification_preferences_updated_at BEFORE UPDATE ON user_notification_preferences FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_notification_rules_updated_at BEFORE UPDATE ON notification_rules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_notification_statistics_updated_at BEFORE UPDATE ON notification_statistics FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_webhook_subscriptions_updated_at BEFORE UPDATE ON webhook_subscriptions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Insert default notification templates
INSERT INTO notification_templates (name, description, template_type, subject_template, body_template, is_system, category, variables) VALUES
    ('job_completion_email', 'Job completion notification email', 'email', 
     'Job Completed: {{job_name}}', 
     'Your job "{{job_name}}" has completed successfully.\n\nExecution Time: {{duration}}\nTarget: {{target_name}}\nStatus: {{status}}\n\nView details: {{job_url}}',
     true, 'job_completion',
     '{"job_name": "Name of the job", "duration": "Execution duration", "target_name": "Target system name", "status": "Execution status", "job_url": "Link to job details"}'::jsonb),
    
    ('job_failure_email', 'Job failure notification email', 'email',
     'Job Failed: {{job_name}}',
     'Your job "{{job_name}}" has failed.\n\nError: {{error_message}}\nTarget: {{target_name}}\nDuration: {{duration}}\n\nView details: {{job_url}}',
     true, 'job_failure',
     '{"job_name": "Name of the job", "error_message": "Error details", "target_name": "Target system name", "duration": "Execution duration", "job_url": "Link to job details"}'::jsonb),
    
    ('system_alert_email', 'System alert notification', 'email',
     'System Alert: {{alert_type}}',
     'A system alert has been triggered.\n\nAlert Type: {{alert_type}}\nSeverity: {{severity}}\nMessage: {{message}}\n\nTime: {{timestamp}}',
     true, 'system_alert',
     '{"alert_type": "Type of alert", "severity": "Alert severity", "message": "Alert message", "timestamp": "When the alert occurred"}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Insert default notification channel for email (requires configuration)
INSERT INTO notification_channels (name, description, channel_type, configuration, is_default) VALUES
    ('default_email', 'Default email channel', 'email',
     '{"smtp_host": "localhost", "smtp_port": 587, "use_tls": true, "from_email": "noreply@opsconductor.local", "from_name": "OpsConductor"}'::jsonb,
     true)
ON CONFLICT (name) DO NOTHING;