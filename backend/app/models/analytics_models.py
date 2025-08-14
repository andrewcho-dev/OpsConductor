"""
Analytics data models for OpsConductor Platform.
These models store aggregated metrics and performance data for reporting.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum


class MetricType(str, enum.Enum):
    JOB_EXECUTION = "job_execution"
    TARGET_PERFORMANCE = "target_performance"
    SYSTEM_UTILIZATION = "system_utilization"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"


class AggregationPeriod(str, enum.Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class PerformanceMetric(Base):
    """
    Time-series performance metrics for analytics and reporting.
    Stores aggregated data points for efficient querying.
    """
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    aggregation_period = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Identifiers for what this metric relates to
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=True, index=True)
    
    # Metric values
    count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_duration = Column(Float, nullable=True)
    min_duration = Column(Float, nullable=True)
    max_duration = Column(Float, nullable=True)
    p95_duration = Column(Float, nullable=True)
    
    # Additional metric data as JSON
    metric_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships - commented out to fix import issues
    # job = relationship("Job", foreign_keys=[job_id])
    # target = relationship("UniversalTarget", foreign_keys=[target_id])

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_metrics_type_period_time', 'metric_type', 'aggregation_period', 'timestamp'),
        Index('idx_metrics_job_time', 'job_id', 'timestamp'),
        Index('idx_metrics_target_time', 'target_id', 'timestamp'),
    )


class SystemHealthSnapshot(Base):
    """
    System health snapshots taken at regular intervals.
    Provides system-wide performance and utilization metrics.
    """
    __tablename__ = "system_health_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # System metrics
    active_jobs = Column(Integer, default=0)
    queued_jobs = Column(Integer, default=0)
    total_targets = Column(Integer, default=0)
    healthy_targets = Column(Integer, default=0)
    warning_targets = Column(Integer, default=0)
    critical_targets = Column(Integer, default=0)
    
    # Performance metrics
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_percent = Column(Float, nullable=True)
    disk_usage_percent = Column(Float, nullable=True)
    network_io_mbps = Column(Float, nullable=True)
    
    # Queue metrics
    job_queue_size = Column(Integer, default=0)
    avg_queue_wait_time = Column(Float, nullable=True)
    
    # Additional system data
    system_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalyticsAlertRule(Base):
    """
    Configurable alert rules for monitoring and notifications.
    Defines thresholds and conditions for automated alerting.
    """
    __tablename__ = "analytics_alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Rule configuration
    metric_type = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)  # gt, lt, eq, gte, lte
    threshold_value = Column(Float, nullable=False)
    evaluation_period = Column(Integer, default=5)  # minutes
    
    # Alert configuration
    is_active = Column(Integer, default=1)
    severity = Column(String(20), default="warning")  # info, warning, critical
    notification_channels = Column(JSON, nullable=True)  # email, webhook, etc.
    
    # Tracking
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ReportTemplate(Base):
    """
    Configurable report templates for scheduled reporting.
    Defines report structure, data sources, and delivery options.
    """
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    report_type = Column(String(50), nullable=False)  # executive, operational, compliance
    
    # Report configuration
    data_sources = Column(JSON, nullable=False)  # Which metrics to include
    time_range = Column(String(20), default="last_7_days")
    format = Column(String(20), default="json")  # json, pdf, csv
    
    # Scheduling
    is_scheduled = Column(Integer, default=0)
    schedule_cron = Column(String(100), nullable=True)
    recipients = Column(JSON, nullable=True)
    
    # Template data
    template_config = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GeneratedReport(Base):
    """
    Generated reports with metadata and storage information.
    Tracks report generation history and provides access to reports.
    """
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    name = Column(String(200), nullable=False)
    
    # Report metadata
    report_period_start = Column(DateTime(timezone=True), nullable=False)
    report_period_end = Column(DateTime(timezone=True), nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Report data
    report_data = Column(JSON, nullable=True)  # For JSON reports
    file_path = Column(String(500), nullable=True)  # For file-based reports
    file_size = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), default="generating")  # generating, completed, failed
    error_message = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    template = relationship("ReportTemplate")
    generated_by_user = relationship("User", foreign_keys=[generated_by])