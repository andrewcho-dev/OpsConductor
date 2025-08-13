# Actions Workspace Guide

## Overview

The Actions Workspace is OpsConductor's comprehensive workflow designer that enables you to create sophisticated automation workflows with conditional logic, dependencies, and advanced error handling. This guide covers all aspects of using the Actions Workspace to build enterprise-grade automation workflows.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Action Types](#action-types)
3. [Conditional Logic](#conditional-logic)
4. [Dependencies & Execution Flow](#dependencies--execution-flow)
5. [Variables & Templating](#variables--templating)
6. [Workflow Settings](#workflow-settings)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

## Getting Started

### Accessing the Actions Workspace

1. Navigate to **Jobs** → **Create New Job**
2. Enter job name and description
3. Select target systems/servers
4. Click **Configure Actions** to open the Actions Workspace

### Workspace Layout

The Actions Workspace features a three-panel layout:

- **Left Panel**: Action type palette with available action types
- **Center Panel**: Drag-and-drop workflow designer
- **Right Panel**: Configuration panel for selected actions

### Basic Workflow Creation

1. **Add Actions**: Drag action types from the left palette to the center workflow area
2. **Configure Actions**: Click on actions to configure parameters in the right panel
3. **Set Order**: Drag actions to reorder execution sequence
4. **Add Logic**: Configure conditions, dependencies, and retry logic
5. **Validate**: Review workflow validation in the Settings tab

## Action Types

### 🖥️ System Commands

Execute shell commands on target systems.

**Configuration Options:**
- **Command**: The command to execute
- **Working Directory**: Directory to run the command in
- **Expected Exit Codes**: Comma-separated list of acceptable exit codes (default: 0)

**Example:**
```bash
# System health check
df -h && free -m && uptime

# Service management
systemctl status nginx && systemctl restart nginx
```

### 📜 Script Execution

Run scripts in various languages with full parameter support.

**Supported Script Types:**
- Bash
- Python
- PowerShell
- Batch
- JavaScript (Node.js)

**Configuration Options:**
- **Script Type**: Language/interpreter
- **Script Content**: The script code
- **Arguments**: Command-line arguments

**Example:**
```python
#!/usr/bin/env python3
import sys
import subprocess

def check_service(service_name):
    result = subprocess.run(['systemctl', 'is-active', service_name], 
                          capture_output=True, text=True)
    return result.returncode == 0

if __name__ == "__main__":
    service = sys.argv[1] if len(sys.argv) > 1 else "nginx"
    if check_service(service):
        print(f"✅ {service} is running")
    else:
        print(f"❌ {service} is not running")
        sys.exit(1)
```

### 🌐 REST API Calls

Make HTTP requests to REST APIs with full header and body support.

**Configuration Options:**
- **Method**: GET, POST, PUT, DELETE, PATCH
- **URL**: API endpoint URL
- **Headers**: JSON object with request headers
- **Request Body**: JSON request payload

**Example:**
```json
{
  "method": "POST",
  "url": "https://api.example.com/deployments",
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}",
    "Content-Type": "application/json"
  },
  "body": {
    "environment": "production",
    "version": "${DEPLOYMENT_VERSION}",
    "targets": ["${TARGET_HOST}"]
  }
}
```

### 🗄️ Database Operations

Execute SQL queries and stored procedures.

**Configuration Options:**
- **Connection String**: Database connection URL
- **Query Type**: SELECT, INSERT, UPDATE, DELETE, Stored Procedure
- **SQL Query**: The SQL statement to execute

**Example:**
```sql
-- Update deployment status
UPDATE deployments 
SET status = 'completed', 
    completed_at = NOW() 
WHERE job_id = '${JOB_NAME}' 
  AND target_host = '${TARGET_HOST}';
```

### 📁 File Operations

Perform file system operations with permission handling.

**Operations:**
- Copy files/directories
- Move files/directories
- Delete files/directories
- Change permissions (chmod)
- Change ownership (chown)
- Create directories (mkdir)

**Configuration Options:**
- **Operation**: Type of file operation
- **Source Path**: Source file/directory path
- **Destination Path**: Destination path
- **Preserve Permissions**: Maintain original permissions

### 📧 Email/Notifications

Send email notifications with templating support.

**Configuration Options:**
- **To**: Comma-separated email addresses
- **Subject**: Email subject line
- **Body**: Email content with variable substitution

**Example:**
```
Subject: Deployment Complete - ${JOB_NAME}

The deployment job "${JOB_NAME}" has completed successfully on ${TARGET_HOST}.

Execution Details:
- Job ID: ${EXECUTION_ID}
- Start Time: ${EXECUTION_TIME}
- Duration: ${EXECUTION_DURATION}
- Status: Success

All systems are operational.
```

### 🔀 Conditional Logic

Create branching logic based on runtime conditions.

**Condition Types:**
- **If/Then**: Simple conditional execution
- **Switch/Case**: Multiple condition branches
- **While Loop**: Repeat until condition is false
- **For Loop**: Iterate over collections

**Available Variables:**
- `${PREVIOUS_ACTION_EXIT_CODE}` - Exit code of previous action
- `${PREVIOUS_ACTION_OUTPUT}` - Output of previous action
- `${TARGET_OS}` - Operating system of target
- `${JOB_NAME}` - Name of current job
- `${EXECUTION_ID}` - Unique execution ID

### ⚡ Parallel Execution

Execute multiple actions concurrently.

**Configuration Options:**
- **Max Concurrency**: Maximum number of parallel actions
- **Wait for All**: Whether to wait for all parallel actions to complete

## Conditional Logic

### Setting Up Conditions

Each action can have multiple conditions that determine whether it should execute:

1. **Variable**: Choose from system or custom variables
2. **Operator**: Select comparison operator (==, !=, >, <, contains, matches)
3. **Value**: The value to compare against

### Condition Examples

```
# Only run if previous action succeeded
Variable: PREVIOUS_ACTION_EXIT_CODE
Operator: ==
Value: 0

# Only run on Linux systems
Variable: TARGET_OS
Operator: contains
Value: linux

# Only run if output contains specific text
Variable: PREVIOUS_ACTION_OUTPUT
Operator: contains
Value: "service is running"

# Only run during business hours
Variable: EXECUTION_TIME
Operator: matches
Value: ^(09|10|11|12|13|14|15|16|17):.*
```

### Multiple Conditions

Actions can have multiple conditions with implicit AND logic. All conditions must be true for the action to execute.

## Dependencies & Execution Flow

### Action Dependencies

Define which actions must complete before others can run:

1. **Action Name/ID**: Reference to the prerequisite action
2. **Required Status**: What status the dependency must have
   - **Success**: Action completed successfully
   - **Failure**: Action failed
   - **Completed**: Action finished (any status)
   - **Skipped**: Action was skipped

### Execution Flow Examples

```
Sequential Flow:
Action 1 → Action 2 → Action 3

Parallel Flow:
Action 1 → [Action 2A, Action 2B, Action 2C] → Action 3

Conditional Flow:
Action 1 → (if success) Action 2A
        → (if failure) Action 2B
```

### Dependency Validation

The system automatically validates:
- **Circular Dependencies**: Prevents infinite loops
- **Missing Dependencies**: Ensures referenced actions exist
- **Unreachable Actions**: Identifies actions that can never execute

## Variables & Templating

### System Variables

Automatically available in all actions:

| Variable | Description |
|----------|-------------|
| `${JOB_NAME}` | Name of the current job |
| `${EXECUTION_ID}` | Unique execution identifier |
| `${TARGET_HOST}` | Current target hostname |
| `${TARGET_OS}` | Target operating system |
| `${EXECUTION_TIME}` | Job execution start time |
| `${PREVIOUS_ACTION_EXIT_CODE}` | Exit code of previous action |
| `${PREVIOUS_ACTION_OUTPUT}` | Output of previous action |

### Custom Variables

Define reusable variables for your workflows:

1. **Variable Name**: Uppercase with underscores (e.g., `MY_VARIABLE`)
2. **Type**: string, number, boolean, or JSON
3. **Default Value**: Value to use if not overridden
4. **Description**: Documentation for the variable

### Variable Usage

Variables can be used in any text field using `${VARIABLE_NAME}` syntax:

```bash
# In commands
echo "Deploying ${APP_NAME} version ${VERSION} to ${TARGET_HOST}"

# In file paths
cp /tmp/${APP_NAME}-${VERSION}.tar.gz /opt/apps/

# In API URLs
https://api.example.com/apps/${APP_NAME}/deploy?version=${VERSION}

# In conditions
${PREVIOUS_ACTION_EXIT_CODE} == 0
```

## Workflow Settings

### Execution Settings

- **Continue on Error**: Whether to continue workflow if actions fail
- **Parallel Execution**: Enable parallel execution where possible
- **Global Timeout**: Maximum time for entire workflow
- **Global Retry Count**: Default retry count for all actions
- **Execution Mode**: Sequential, parallel, or batch execution

### Logging & Monitoring

- **Log Level**: debug, info, warning, error
- **Capture Output**: Save action output for debugging
- **Enable Notifications**: Send completion notifications

### Advanced Options

- **Environment Variables**: Custom environment variables (JSON format)
- **Workflow Tags**: Tags for categorization and filtering

## Best Practices

### Workflow Design

1. **Start Simple**: Begin with basic sequential workflows
2. **Use Descriptive Names**: Give actions clear, descriptive names
3. **Add Documentation**: Use action descriptions to document purpose
4. **Test Incrementally**: Test workflows on non-production systems first

### Error Handling

1. **Set Appropriate Timeouts**: Prevent workflows from hanging
2. **Use Retry Logic**: Handle transient failures automatically
3. **Plan for Failures**: Design rollback actions for critical operations
4. **Monitor Dependencies**: Ensure dependency chains are logical

### Performance

1. **Use Parallel Execution**: Run independent actions concurrently
2. **Optimize Commands**: Use efficient commands and scripts
3. **Limit Concurrency**: Don't overwhelm target systems
4. **Cache Results**: Store results in variables for reuse

### Security

1. **Use Variables**: Store sensitive data in variables, not hardcoded
2. **Validate Inputs**: Check variable values before use
3. **Limit Permissions**: Use least-privilege principles
4. **Audit Workflows**: Review workflows for security issues

## Examples

### Example 1: Web Application Deployment

```
1. Pre-deployment Health Check (command)
   └─ Command: curl -f http://${TARGET_HOST}/health
   └─ Condition: None

2. Stop Application Service (command)
   └─ Command: systemctl stop myapp
   └─ Dependency: Action 1 (success)

3. Backup Current Version (script)
   └─ Script: backup_application.sh ${APP_NAME}
   └─ Dependency: Action 2 (success)

4. Deploy New Version (file operation)
   └─ Operation: Copy
   └─ Source: /tmp/${APP_NAME}-${VERSION}.tar.gz
   └─ Destination: /opt/apps/
   └─ Dependency: Action 3 (success)

5. Update Configuration (script)
   └─ Script: update_config.py --version=${VERSION}
   └─ Dependency: Action 4 (success)

6. Start Application Service (command)
   └─ Command: systemctl start myapp
   └─ Dependency: Action 5 (success)

7. Post-deployment Health Check (command)
   └─ Command: curl -f http://${TARGET_HOST}/health
   └─ Dependency: Action 6 (success)
   └─ Retry: 3 times, 10 second delay

8. Send Success Notification (email)
   └─ To: ops-team@company.com
   └─ Subject: Deployment Success - ${APP_NAME} ${VERSION}
   └─ Dependency: Action 7 (success)

9. Rollback on Failure (script)
   └─ Script: rollback_deployment.sh ${APP_NAME}
   └─ Condition: PREVIOUS_ACTION_EXIT_CODE != 0
   └─ Dependency: Action 7 (failure)
```

### Example 2: Database Maintenance

```
1. Check Database Connection (database)
   └─ Query: SELECT 1
   └─ Connection: postgresql://user:pass@${TARGET_HOST}:5432/db

2. Create Backup (command)
   └─ Command: pg_dump -h ${TARGET_HOST} mydb > backup_${EXECUTION_TIME}.sql
   └─ Dependency: Action 1 (success)

3. Run Maintenance Tasks (parallel)
   ├─ 3A. Update Statistics (database)
   │   └─ Query: ANALYZE;
   ├─ 3B. Vacuum Tables (database)
   │   └─ Query: VACUUM;
   └─ 3C. Reindex (database)
       └─ Query: REINDEX DATABASE mydb;
   └─ Dependencies: Action 2 (success)

4. Verify Database Health (database)
   └─ Query: SELECT COUNT(*) FROM pg_stat_activity;
   └─ Dependencies: Actions 3A, 3B, 3C (all success)

5. Send Report (email)
   └─ To: dba-team@company.com
   └─ Subject: Database Maintenance Complete - ${TARGET_HOST}
   └─ Body: Maintenance completed successfully. Backup: backup_${EXECUTION_TIME}.sql
   └─ Dependency: Action 4 (success)
```

### Example 3: Infrastructure Monitoring

```
1. System Resource Check (command)
   └─ Command: df -h && free -m && uptime
   └─ Condition: None

2. Service Status Check (script)
   └─ Script: check_services.py nginx mysql redis
   └─ Dependency: Action 1 (completed)

3. Log Analysis (command)
   └─ Command: tail -n 100 /var/log/syslog | grep ERROR
   └─ Dependency: Action 1 (completed)

4. Performance Metrics (API)
   └─ Method: POST
   └─ URL: https://monitoring.company.com/api/metrics
   └─ Body: {"host": "${TARGET_HOST}", "timestamp": "${EXECUTION_TIME}"}
   └─ Dependencies: Actions 1, 2, 3 (all completed)

5. Alert on Issues (conditional)
   └─ Condition: PREVIOUS_ACTION_OUTPUT contains "ERROR"
   └─ Dependency: Action 3 (success)

6. Send Alert Email (email)
   └─ To: ops-team@company.com
   └─ Subject: ALERT - Issues detected on ${TARGET_HOST}
   └─ Dependency: Action 5 (success)

7. Create Ticket (API)
   └─ Method: POST
   └─ URL: https://ticketing.company.com/api/tickets
   └─ Body: {"title": "System issues on ${TARGET_HOST}", "priority": "high"}
   └─ Dependency: Action 5 (success)
```

## Troubleshooting

### Common Issues

1. **Action Not Executing**
   - Check conditions are met
   - Verify dependencies are satisfied
   - Review timeout settings

2. **Variable Not Substituting**
   - Ensure variable name is correct
   - Check variable is defined
   - Verify syntax: `${VARIABLE_NAME}`

3. **Circular Dependencies**
   - Review dependency chain
   - Use workflow validation
   - Redesign execution flow

4. **Performance Issues**
   - Reduce parallel concurrency
   - Optimize commands/scripts
   - Increase timeouts

### Getting Help

- Use the workflow validation feature
- Check execution logs for detailed error messages
- Review the API reference for technical details
- Contact support for complex issues

---

*This guide covers the comprehensive features of the OpsConductor Actions Workspace. For additional help, refer to the API documentation or contact support.*