-- ENABLEDRM Analytics Tables
-- This script creates analytics and reporting tables for performance monitoring

-- Performance metrics table for time-series analytics data
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    aggregation_period VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Foreign key references
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES universal_targets(id) ON DELETE CASCADE,
    
    -- Metric values
    count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration FLOAT,
    min_duration FLOAT,
    max_duration FLOAT,
    p95_duration FLOAT,
    
    -- Additional metric data as JSON
    metric_data JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System health snapshots for monitoring
CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- System metrics
    active_jobs INTEGER DEFAULT 0,
    queued_jobs INTEGER DEFAULT 0,
    total_targets INTEGER DEFAULT 0,
    healthy_targets INTEGER DEFAULT 0,
    warning_targets INTEGER DEFAULT 0,
    critical_targets INTEGER DEFAULT 0,
    
    -- Performance metrics
    cpu_usage_percent FLOAT,
    memory_usage_percent FLOAT,
    disk_usage_percent FLOAT,
    network_io_mbps FLOAT,
    
    -- Queue metrics
    job_queue_size INTEGER DEFAULT 0,
    avg_queue_wait_time FLOAT,
    
    -- Additional system data
    system_data JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert rules for automated monitoring
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    
    -- Rule configuration
    metric_type VARCHAR(50) NOT NULL,
    condition VARCHAR(20) NOT NULL, -- gt, lt, eq, gte, lte
    threshold_value FLOAT NOT NULL,
    evaluation_period INTEGER DEFAULT 5, -- minutes
    
    -- Alert configuration
    is_active INTEGER DEFAULT 1,
    severity VARCHAR(20) DEFAULT 'warning', -- info, warning, critical
    notification_channels JSONB,
    
    -- Tracking
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Report templates for scheduled reporting
CREATE TABLE IF NOT EXISTS report_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    report_type VARCHAR(50) NOT NULL, -- executive, operational, compliance
    
    -- Report configuration
    data_sources JSONB NOT NULL,
    time_range VARCHAR(20) DEFAULT 'last_7_days',
    format VARCHAR(20) DEFAULT 'json', -- json, pdf, csv
    
    -- Scheduling
    is_scheduled INTEGER DEFAULT 0,
    schedule_cron VARCHAR(100),
    recipients JSONB,
    
    -- Template data
    template_config JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Generated reports history
CREATE TABLE IF NOT EXISTS generated_reports (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES report_templates(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    
    -- Report metadata
    report_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    report_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    generated_by INTEGER, -- References user from user-service
    
    -- Report data
    report_data JSONB,
    file_path VARCHAR(500),
    file_size INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'generating', -- generating, completed, failed
    error_message VARCHAR(1000),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type_period_time 
    ON performance_metrics(metric_type, aggregation_period, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_job_time 
    ON performance_metrics(job_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_target_time 
    ON performance_metrics(target_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_system_health_timestamp 
    ON system_health_snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_alert_rules_active 
    ON alert_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_generated_reports_template 
    ON generated_reports(template_id);
CREATE INDEX IF NOT EXISTS idx_generated_reports_period 
    ON generated_reports(report_period_start, report_period_end);

-- Insert default alert rules
INSERT INTO alert_rules (name, description, metric_type, condition, threshold_value, severity) VALUES
('High Job Failure Rate', 'Alert when job failure rate exceeds 10%', 'job_execution', 'gt', 10.0, 'warning'),
('Very High Job Failure Rate', 'Alert when job failure rate exceeds 25%', 'job_execution', 'gt', 25.0, 'critical'),
('Low Target Availability', 'Alert when target availability drops below 90%', 'target_performance', 'lt', 90.0, 'warning'),
('Critical Target Availability', 'Alert when target availability drops below 75%', 'target_performance', 'lt', 75.0, 'critical'),
('High Queue Size', 'Alert when job queue size exceeds 50 jobs', 'system_utilization', 'gt', 50.0, 'warning'),
('Very High Queue Size', 'Alert when job queue size exceeds 100 jobs', 'system_utilization', 'gt', 100.0, 'critical')
ON CONFLICT DO NOTHING;

-- Insert default report templates
INSERT INTO report_templates (name, description, report_type, data_sources, time_range) VALUES
('Daily Executive Summary', 'Daily summary of job execution and system performance', 'executive', 
 '{"job_metrics": true, "target_metrics": true, "system_metrics": true, "trends": true}', 'last_1_day'),
('Weekly Operations Report', 'Weekly detailed operations report with performance analysis', 'operational',
 '{"job_performance": true, "target_performance": true, "error_analysis": true, "trends": true}', 'last_7_days'),
('Monthly Executive Report', 'Monthly high-level executive summary with KPIs and trends', 'executive',
 '{"kpis": true, "trends": true, "recommendations": true}', 'last_30_days'),
('Compliance Audit Report', 'Comprehensive audit trail and compliance report', 'compliance',
 '{"audit_logs": true, "user_activity": true, "security_events": true}', 'last_30_days')
ON CONFLICT DO NOTHING;

-- Create a view for easy analytics queries
CREATE OR REPLACE VIEW analytics_summary AS
SELECT 
    DATE(je.created_at) as execution_date,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN je.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN je.status = 'failed' THEN 1 END) as failed_executions,
    COUNT(CASE WHEN je.status = 'cancelled' THEN 1 END) as cancelled_executions,
    ROUND(
        COUNT(CASE WHEN je.status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2
    ) as success_rate,
    AVG(
        CASE WHEN je.started_at IS NOT NULL AND je.completed_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (je.completed_at - je.started_at))
        END
    ) as avg_duration_seconds
FROM job_executions je
WHERE je.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(je.created_at)
ORDER BY execution_date DESC;

-- Create a view for target performance summary
CREATE OR REPLACE VIEW target_performance_summary AS
SELECT 
    ut.id as target_id,
    ut.name as target_name,
    ut.target_type,
    ut.os_type,
    ut.environment,
    ut.health_status,
    COUNT(jeb.id) as total_executions,
    COUNT(CASE WHEN jeb.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN jeb.status = 'failed' THEN 1 END) as failed_executions,
    ROUND(
        COUNT(CASE WHEN jeb.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(jeb.id), 0), 2
    ) as success_rate,
    AVG(
        CASE WHEN jeb.started_at IS NOT NULL AND jeb.completed_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (jeb.completed_at - jeb.started_at))
        END
    ) as avg_response_time_seconds
FROM universal_targets ut
LEFT JOIN job_execution_branches jeb ON ut.id = jeb.target_id
    AND jeb.created_at >= CURRENT_DATE - INTERVAL '30 days'
WHERE ut.is_active = TRUE
GROUP BY ut.id, ut.name, ut.target_type, ut.os_type, ut.environment, ut.health_status
ORDER BY success_rate DESC NULLS LAST;