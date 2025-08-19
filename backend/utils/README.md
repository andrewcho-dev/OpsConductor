# Utility Scripts

This directory contains utility scripts for various maintenance and debugging tasks.

## Debugging Scripts

- `debug_action_execution.py` - Debug action execution issues
- `debug_full_stack_trace.py` - Generate full stack traces for debugging
- `debug_job_execution.py` - Debug job execution issues
- `debug_method_config_error.py` - Debug method configuration errors

## Maintenance Scripts

- `cleanup_stale_executions.py` - Clean up stale job executions
- `create_admin_user.py` - Create an admin user
- `create_notification_tables.py` - Create notification tables

## Fix Scripts

- `fix_all_quotes.py` - Fix quote issues in code
- `fix_auth.py` - Fix authentication issues
- `fix_auth_universal_targets.py` - Fix authentication for universal targets
- `fix_quotes.py` - Fix quote issues in specific files
- `fix_remaining_auth.py` - Fix remaining authentication issues
- `fix_stuck_executions.py` - Fix stuck job executions

## Usage

These scripts should be run from the backend directory:

```bash
cd /home/enabledrm/backend
python -m utils.script_name
```

For example:

```bash
python -m utils.create_admin_user
```