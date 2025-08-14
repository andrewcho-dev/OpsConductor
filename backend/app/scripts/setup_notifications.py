#!/usr/bin/env python3
"""
Setup script for notification system
Creates default notification templates and alert rules
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.notification_models import NotificationTemplate, AlertRule
from app.services.system_service import SystemService


def create_default_templates(db: Session):
    """Create default notification templates"""
    
    templates = [
        {
            "name": "job_failure_alert",
            "subject_template": "EnableDRM Alert: Job {{job_name}} Failed",
            "body_template": """
Job Failure Alert

Job Name: {{job_name}}
Job ID: {{job_id}}
Status: {{status}}
Error: {{error_message}}
Target: {{target_name}}
Started: {{started_at}}
Failed: {{failed_at}}

Please review the job execution and take appropriate action.

---
EnableDRM Universal Automation Platform
            """.strip(),
            "template_type": "email",
            "description": "Template for job failure notifications"
        },
        {
            "name": "system_error_alert",
            "subject_template": "EnableDRM System Error: {{error_type}}",
            "body_template": """
System Error Alert

Error Type: {{error_type}}
Severity: {{severity}}
Message: {{message}}
Timestamp: {{timestamp}}
Component: {{component}}

Context Data:
{{context_data}}

Please investigate this system error immediately.

---
EnableDRM Universal Automation Platform
            """.strip(),
            "template_type": "email",
            "description": "Template for system error notifications"
        },
        {
            "name": "performance_alert",
            "subject_template": "EnableDRM Performance Alert: {{metric_name}}",
            "body_template": """
Performance Alert

Metric: {{metric_name}}
Current Value: {{current_value}}
Threshold: {{threshold}}
Severity: {{severity}}
Timestamp: {{timestamp}}

Description: {{description}}

Please review system performance and take action if necessary.

---
EnableDRM Universal Automation Platform
            """.strip(),
            "template_type": "email",
            "description": "Template for performance alerts"
        },
        {
            "name": "security_alert",
            "subject_template": "EnableDRM Security Alert: {{security_event}}",
            "body_template": """
Security Alert

Event: {{security_event}}
Severity: {{severity}}
Source: {{source}}
Timestamp: {{timestamp}}
User: {{user}}

Details: {{details}}

This security event requires immediate attention.

---
EnableDRM Universal Automation Platform
            """.strip(),
            "template_type": "email",
            "description": "Template for security alerts"
        },
        {
            "name": "job_completion_notification",
            "subject_template": "EnableDRM Job Complete: {{job_name}}",
            "body_template": """
Job Completion Notification

Job Name: {{job_name}}
Job ID: {{job_id}}
Status: {{status}}
Target: {{target_name}}
Started: {{started_at}}
Completed: {{completed_at}}
Duration: {{duration}}

Results: {{results}}

---
EnableDRM Universal Automation Platform
            """.strip(),
            "template_type": "email",
            "description": "Template for job completion notifications"
        }
    ]
    
    for template_data in templates:
        # Check if template already exists
        existing = db.query(NotificationTemplate).filter(
            NotificationTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = NotificationTemplate(**template_data)
            db.add(template)
            print(f"Created template: {template_data['name']}")
        else:
            print(f"Template already exists: {template_data['name']}")
    
    db.commit()


def create_default_alert_rules(db: Session):
    """Create default alert rules"""
    
    # Get template IDs
    job_failure_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == "job_failure_alert"
    ).first()
    
    system_error_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == "system_error_alert"
    ).first()
    
    performance_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == "performance_alert"
    ).first()
    
    security_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == "security_alert"
    ).first()
    
    rules = [
        {
            "name": "job_failure_notifications",
            "description": "Send notifications when jobs fail",
            "alert_type": "job_failure",
            "trigger_condition": {
                "min_severity": "error",
                "include_warnings": False
            },
            "recipients": ["admin@opsconductor.com"],
            "notification_template_id": job_failure_template.id if job_failure_template else None
        },
        {
            "name": "system_error_notifications",
            "description": "Send notifications for system errors",
            "alert_type": "system_error",
            "trigger_condition": {
                "min_severity": "error",
                "include_warnings": True
            },
            "recipients": ["admin@opsconductor.com", "ops@opsconductor.com"],
            "notification_template_id": system_error_template.id if system_error_template else None
        },
        {
            "name": "performance_alerts",
            "description": "Send notifications for performance issues",
            "alert_type": "performance",
            "trigger_condition": {
                "min_severity": "warning",
                "include_info": False
            },
            "recipients": ["admin@opsconductor.com"],
            "notification_template_id": performance_template.id if performance_template else None
        },
        {
            "name": "security_alerts",
            "description": "Send notifications for security events",
            "alert_type": "security",
            "trigger_condition": {
                "min_severity": "warning",
                "include_info": True
            },
            "recipients": ["admin@opsconductor.com", "security@opsconductor.com"],
            "notification_template_id": security_template.id if security_template else None
        }
    ]
    
    for rule_data in rules:
        # Check if rule already exists
        existing = db.query(AlertRule).filter(
            AlertRule.name == rule_data["name"]
        ).first()
        
        if not existing:
            rule = AlertRule(**rule_data)
            db.add(rule)
            print(f"Created alert rule: {rule_data['name']}")
        else:
            print(f"Alert rule already exists: {rule_data['name']}")
    
    db.commit()


def setup_default_smtp_settings(db: Session):
    """Set up default SMTP settings if not configured"""
    system_service = SystemService(db)
    
    # Check if SMTP is already configured
    smtp_host = system_service.get_setting('smtp_host')
    if not smtp_host:
        print("Setting up default SMTP settings...")
        print("Please configure your SMTP settings via the API or environment variables:")
        print("  - SMTP_HOST: Your SMTP server hostname")
        print("  - SMTP_PORT: SMTP server port (default: 587)")
        print("  - SMTP_USERNAME: SMTP username")
        print("  - SMTP_PASSWORD: SMTP password")
        print("  - SMTP_USE_TLS: Use TLS (default: true)")
        print("  - SMTP_USE_SSL: Use SSL (default: false)")
        
        # Set some defaults
        system_service.set_setting('smtp_port', 587, 'SMTP server port')
        system_service.set_setting('smtp_use_tls', True, 'Use TLS for SMTP')
        system_service.set_setting('smtp_use_ssl', False, 'Use SSL for SMTP')
        
        print("Default SMTP settings configured. Please update with your actual SMTP server details.")
    else:
        print(f"SMTP already configured with host: {smtp_host}")


def main():
    """Main setup function"""
    print("Setting up EnableDRM notification system...")
    
    db = SessionLocal()
    try:
        # Create default templates
        print("\n1. Creating notification templates...")
        create_default_templates(db)
        
        # Create default alert rules
        print("\n2. Creating alert rules...")
        create_default_alert_rules(db)
        
        # Setup SMTP settings
        print("\n3. Setting up SMTP configuration...")
        setup_default_smtp_settings(db)
        
        print("\n✅ Notification system setup complete!")
        print("\nNext steps:")
        print("1. Configure your SMTP settings via the API or environment variables")
        print("2. Test email configuration using the /api/notifications/smtp/test endpoint")
        print("3. Update alert rule recipients with actual email addresses")
        print("4. Customize notification templates as needed")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
