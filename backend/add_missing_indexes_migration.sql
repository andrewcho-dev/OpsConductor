-- Migration: Add Missing Foreign Key Indexes
-- This migration adds critical indexes for foreign key columns to improve query performance

-- Add indexes for foreign keys that are missing them
CREATE INDEX IF NOT EXISTS idx_alert_logs_alert_rule_id ON alert_logs(alert_rule_id);
CREATE INDEX IF NOT EXISTS idx_device_type_templates_created_by ON device_type_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_device_type_usage_user_id ON device_type_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_device_types_created_by ON device_types(created_by);
CREATE INDEX IF NOT EXISTS idx_discovery_schedules_created_by ON discovery_schedules(created_by);
CREATE INDEX IF NOT EXISTS idx_discovery_templates_created_by ON discovery_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_generated_reports_generated_by ON generated_reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_job_action_results_action_id ON job_action_results(action_id);
CREATE INDEX IF NOT EXISTS idx_job_action_results_branch_id ON job_action_results(branch_id);
CREATE INDEX IF NOT EXISTS idx_target_credentials_communication_method_id ON target_credentials(communication_method_id);

-- Add some composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_jobs_status_created_by ON jobs(status, created_by);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id_status ON job_executions(job_id, status);
CREATE INDEX IF NOT EXISTS idx_universal_targets_type_environment ON universal_targets(target_type, environment);
CREATE INDEX IF NOT EXISTS idx_job_execution_branches_execution_status ON job_execution_branches(job_execution_id, status);

-- Add indexes for timestamp-based queries (common in analytics)
CREATE INDEX IF NOT EXISTS idx_job_executions_created_at ON job_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_job_execution_logs_timestamp_level ON job_execution_logs(timestamp, log_level);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_health_snapshots_timestamp ON system_health_snapshots(timestamp);

COMMENT ON INDEX idx_alert_logs_alert_rule_id IS 'Performance index for alert log queries by rule';
COMMENT ON INDEX idx_job_action_results_action_id IS 'Performance index for action result queries';
COMMENT ON INDEX idx_job_action_results_branch_id IS 'Performance index for branch result queries';
COMMENT ON INDEX idx_target_credentials_communication_method_id IS 'Performance index for credential queries by communication method';