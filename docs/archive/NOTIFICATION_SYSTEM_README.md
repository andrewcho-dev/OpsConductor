# EnableDRM Email Notification System

## Overview

The EnableDRM platform includes a comprehensive email notification system that provides:

- **SMTP Email Relay**: Configurable SMTP server for sending emails
- **Notification Templates**: Reusable email templates with variable substitution
- **Alert Rules**: Automated alerts based on system events
- **Alert Management**: Create, track, and resolve system alerts
- **Notification Logging**: Complete audit trail of all sent notifications

## Architecture

The notification system follows the EnableDRM architecture principles:

- **Universal Target Integration**: Email targets are configured as universal targets with SMTP communication methods
- **Job-Centric Design**: Notifications are triggered by job events and system activities
- **Comprehensive Logging**: All notification attempts are logged with detailed status information
- **Template-Based**: Reusable templates with variable substitution for consistent messaging

## Quick Start

### 1. Configure SMTP Settings

#### Option A: Environment Variables
Add these to your `.env` file:

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

#### Option B: API Configuration
Use the API to configure SMTP settings:

```bash
curl -X POST "http://localhost:8000/api/notifications/smtp/config" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "use_tls": true,
    "use_ssl": false
  }'
```

### 2. Test SMTP Configuration

```bash
curl -X POST "http://localhost:8000/api/notifications/smtp/test" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email from EnableDRM"
  }'
```

### 3. Run Setup Script

Initialize default templates and alert rules:

```bash
cd backend
python -m app.scripts.setup_notifications
```

## SMTP Configuration

### Supported SMTP Providers

#### Gmail
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not regular password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

#### Outlook/Hotmail
```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

#### Office 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

#### Custom SMTP Server
```bash
SMTP_HOST=your-smtp-server.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

### Security Considerations

1. **Use App Passwords**: For Gmail, use App Passwords instead of regular passwords
2. **Environment Variables**: Store SMTP credentials in environment variables, not in code
3. **TLS/SSL**: Always use TLS or SSL for secure email transmission
4. **Credential Rotation**: Regularly rotate SMTP credentials

## API Endpoints

### SMTP Configuration

- `GET /api/notifications/smtp/config` - Get current SMTP configuration
- `POST /api/notifications/smtp/config` - Update SMTP configuration
- `POST /api/notifications/smtp/test` - Test SMTP configuration

### Email Sending

- `POST /api/notifications/email/send` - Send email (direct or templated)

### Notification Templates

- `GET /api/notifications/templates` - List notification templates
- `POST /api/notifications/templates` - Create notification template
- `GET /api/notifications/templates/{id}` - Get template by ID
- `PUT /api/notifications/templates/{id}` - Update template
- `DELETE /api/notifications/templates/{id}` - Delete template

### Alert Rules

- `GET /api/notifications/alerts/rules` - List alert rules
- `POST /api/notifications/alerts/rules` - Create alert rule
- `GET /api/notifications/alerts/rules/{id}` - Get rule by ID
- `PUT /api/notifications/alerts/rules/{id}` - Update rule
- `DELETE /api/notifications/alerts/rules/{id}` - Delete rule

### Alert Management

- `POST /api/notifications/alerts` - Create alert
- `GET /api/notifications/alerts` - List alerts with filtering
- `GET /api/notifications/alerts/{id}` - Get alert by ID
- `POST /api/notifications/alerts/{id}/resolve` - Resolve alert

### Logs and Statistics

- `GET /api/notifications/logs` - Get notification logs
- `GET /api/notifications/stats` - Get notification statistics

## Usage Examples

### Send Direct Email

```python
import requests

# Send a simple email
response = requests.post("http://localhost:8000/api/notifications/email/send", json={
    "to_emails": ["user@example.com"],
    "subject": "Test Email",
    "body": "This is a test email from EnableDRM"
})

print(response.json())
```

### Send Templated Email

```python
# Send email using a template
response = requests.post("http://localhost:8000/api/notifications/email/send", json={
    "to_emails": ["admin@example.com"],
    "template_name": "job_failure_alert",
    "template_data": {
        "job_name": "Database Backup",
        "job_id": "12345",
        "status": "failed",
        "error_message": "Connection timeout",
        "target_name": "db-server-01",
        "started_at": "2024-01-15 10:00:00 UTC",
        "failed_at": "2024-01-15 10:05:00 UTC"
    }
})
```

### Create Alert

```python
# Create a system alert
response = requests.post("http://localhost:8000/api/notifications/alerts", json={
    "alert_type": "system_error",
    "severity": "error",
    "message": "Database connection failed",
    "context_data": {
        "component": "database",
        "error_code": "CONNECTION_TIMEOUT",
        "retry_count": 3
    }
})
```

## Notification Templates

### Default Templates

The system includes these default templates:

1. **job_failure_alert** - Job failure notifications
2. **system_error_alert** - System error notifications
3. **performance_alert** - Performance issue notifications
4. **security_alert** - Security event notifications
5. **job_completion_notification** - Job completion notifications

### Template Variables

Templates use `{{variable_name}}` syntax for variable substitution:

```text
Subject: EnableDRM Alert: Job {{job_name}} Failed

Job Name: {{job_name}}
Job ID: {{job_id}}
Status: {{status}}
Error: {{error_message}}
```

### Creating Custom Templates

```python
# Create a custom template
response = requests.post("http://localhost:8000/api/notifications/templates", json={
    "name": "custom_alert",
    "subject_template": "Custom Alert: {{alert_title}}",
    "body_template": """
Custom Alert Notification

Title: {{alert_title}}
Description: {{description}}
Priority: {{priority}}
Timestamp: {{timestamp}}

Please take action as needed.

---
EnableDRM Platform
    """.strip(),
    "template_type": "email",
    "description": "Custom alert template"
})
```

## Alert Rules

### Default Alert Rules

1. **job_failure_notifications** - Triggers on job failures
2. **system_error_notifications** - Triggers on system errors
3. **performance_alerts** - Triggers on performance issues
4. **security_alerts** - Triggers on security events

### Creating Alert Rules

```python
# Create an alert rule
response = requests.post("http://localhost:8000/api/notifications/alerts/rules", json={
    "name": "high_cpu_alert",
    "description": "Alert when CPU usage is high",
    "alert_type": "performance",
    "trigger_condition": {
        "min_severity": "warning",
        "metric": "cpu_usage",
        "threshold": 80
    },
    "recipients": ["admin@example.com", "ops@example.com"],
    "notification_template_id": 3  # performance_alert template
})
```

## Integration with Jobs

### Job Failure Notifications

When a job fails, the system automatically:

1. Creates an alert with type `job_failure`
2. Evaluates alert rules for job failures
3. Sends notifications to configured recipients
4. Logs the notification attempt

### Example Job Integration

```python
# In your job execution code
from app.services.notification_service import NotificationService

def execute_job(job_id, target_id):
    try:
        # Execute job logic
        result = perform_job_operation()
        
        # Send success notification
        notification_service.send_templated_email(
            template_name="job_completion_notification",
            to_emails=["admin@example.com"],
            template_data={
                "job_name": "Database Backup",
                "job_id": job_id,
                "status": "completed",
                "target_name": "db-server-01",
                "started_at": "2024-01-15 10:00:00 UTC",
                "completed_at": "2024-01-15 10:05:00 UTC",
                "duration": "5 minutes",
                "results": "Backup completed successfully"
            }
        )
        
    except Exception as e:
        # Create failure alert
        notification_service.create_alert(
            alert_type="job_failure",
            severity="error",
            message=f"Job {job_id} failed: {str(e)}",
            context_data={
                "job_id": job_id,
                "target_id": target_id,
                "error": str(e)
            }
        )
```

## Monitoring and Troubleshooting

### Check SMTP Configuration

```bash
curl "http://localhost:8000/api/notifications/smtp/config"
```

### View Notification Logs

```bash
curl "http://localhost:8000/api/notifications/logs?limit=10"
```

### View Alert Logs

```bash
curl "http://localhost:8000/api/notifications/alerts?limit=10"
```

### Get Statistics

```bash
curl "http://localhost:8000/api/notifications/stats"
```

### Common Issues

1. **SMTP Authentication Failed**
   - Check username/password
   - For Gmail, use App Password
   - Verify SMTP server settings

2. **Connection Timeout**
   - Check SMTP host and port
   - Verify firewall settings
   - Test network connectivity

3. **TLS/SSL Issues**
   - Ensure correct TLS/SSL settings
   - Check certificate validity
   - Try different port combinations

## Security Best Practices

1. **Credential Management**
   - Use environment variables for credentials
   - Rotate passwords regularly
   - Use App Passwords for cloud providers

2. **Access Control**
   - Limit SMTP configuration access
   - Audit notification logs regularly
   - Monitor for unusual email patterns

3. **Template Security**
   - Validate template variables
   - Sanitize user input
   - Use parameterized templates

## Docker Configuration

When running in Docker, ensure SMTP environment variables are passed to the container:

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_USE_TLS=${SMTP_USE_TLS}
      - SMTP_USE_SSL=${SMTP_USE_SSL}
```

## Support

For issues with the notification system:

1. Check the notification logs: `/api/notifications/logs`
2. Test SMTP configuration: `/api/notifications/smtp/test`
3. Review alert rules and templates
4. Verify environment variable configuration

The notification system is designed to be robust and provide comprehensive logging for troubleshooting.
