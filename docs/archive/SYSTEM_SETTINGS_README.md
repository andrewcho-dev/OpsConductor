# System Settings and Timezone Management

## Overview

The ENABLEDRM platform now includes comprehensive system settings management with a focus on accurate timezone handling and DST (Daylight Saving Time) support. This is critical for job scheduling where users need to be absolutely clear about when jobs will execute.

## Key Features

### 1. Timezone Management
- **System Timezone Configuration**: Set and manage the system's local timezone
- **DST Support**: Automatic handling of daylight saving time transitions
- **UTC Processing**: All internal operations use UTC for consistency
- **Local Display**: Users see times in their configured local timezone

### 2. System Settings
- **Session Timeout**: Configurable user session timeout (60-86400 seconds)
- **Max Concurrent Jobs**: Limit concurrent job executions (1-1000)
- **Log Retention**: Configure log retention period (1-3650 days)
- **Real-time Updates**: Live display of current system time

### 3. Job Scheduling Support
- **Time Validation**: Validate job schedule times with timezone conversion
- **Clear Communication**: Both UTC and local times displayed
- **DST Awareness**: Automatic handling of DST transitions

## Architecture

### Backend Components

#### 1. System Models (`backend/app/models/system_models.py`)
```python
class SystemSetting(Base):
    """System settings model for storing configuration data"""
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TimezoneManager:
    """Manages timezone and DST configuration for the system"""
    # Static methods for timezone operations
```

#### 2. System Service (`backend/app/services/system_service.py`)
```python
class SystemService:
    """Service for managing system settings and configuration"""
    
    def get_timezone(self) -> str
    def set_timezone(self, timezone_name: str) -> bool
    def utc_to_local(self, utc_dt: datetime) -> datetime
    def local_to_utc(self, local_dt: datetime) -> datetime
    def validate_job_schedule_time(self, local_time: datetime) -> Dict[str, Any]
    # ... additional methods
```

#### 3. System Router (`backend/app/routers/system.py`)
```python
# API Endpoints:
GET  /api/system/info              # Get comprehensive system information
GET  /api/system/timezone          # Get current timezone
PUT  /api/system/timezone          # Update timezone
GET  /api/system/timezones         # Get available timezones
GET  /api/system/current-time      # Get current time
POST /api/system/validate-schedule-time  # Validate job schedule time
# ... additional endpoints
```

#### 4. Time Utilities (`backend/app/utils/time_utils.py`)
```python
class TimeUtils:
    """Utility class for timezone and time operations"""
    
class JobScheduleTimeValidator:
    """Validator for job schedule times with timezone awareness"""
    
class TimezoneFormatter:
    """Utility for formatting timezone information"""
```

### Frontend Components

#### System Settings Component (`frontend/src/components/system/SystemSettings.jsx`)
- **Real-time Clock**: Live display of UTC and local time
- **Timezone Selection**: Dropdown with all available timezones
- **Settings Management**: Forms for all system settings
- **Responsive Design**: Works on all screen sizes

## Database Schema

### System Settings Table
```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Default settings:
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('timezone', '"UTC"', 'System timezone configuration'),
('session_timeout', '1800', 'User session timeout in seconds'),
('max_concurrent_jobs', '50', 'Maximum concurrent job executions'),
('log_retention_days', '30', 'How long to keep logs in days');
```

## API Endpoints

### System Information
```http
GET /api/system/info
```
Returns comprehensive system information including timezone, DST status, and current times.

### Timezone Management
```http
GET /api/system/timezone
PUT /api/system/timezone
GET /api/system/timezones
```

### Current Time
```http
GET /api/system/current-time
```
Returns current time in both UTC and local timezone.

### Job Schedule Validation
```http
POST /api/system/validate-schedule-time
Content-Type: application/json

{
  "local_time": "2024-01-15T14:30:00"
}
```

## Usage Examples

### 1. Setting System Timezone
```python
# Backend
service = SystemService(db)
success = service.set_timezone("America/New_York")

# Frontend
await axios.put('/api/system/timezone', { timezone: 'America/New_York' });
```

### 2. Converting Times for Job Scheduling
```python
# Validate and convert local time to UTC
validation = service.validate_job_schedule_time(local_time)
if validation['valid']:
    utc_time = validation['utc_time']
    # Use utc_time for job scheduling
```

### 3. Displaying Times to Users
```python
# Convert UTC time to local display
local_display = service.utc_to_local_string(utc_time)
# Returns: "2024-01-15 09:30:00 EST"
```

## Timezone Handling Rules

### 1. UTC Processing
- **All internal storage**: Times stored in UTC
- **All job execution**: Times processed in UTC
- **Database timestamps**: All stored in UTC

### 2. Local Display
- **User interface**: Times displayed in local timezone
- **Job scheduling**: Users select times in local timezone
- **Logs and reports**: Times shown in local timezone

### 3. DST Handling
- **Automatic detection**: System detects DST transitions
- **No manual intervention**: DST handled automatically
- **Clear communication**: DST status shown to users

## Configuration

### Environment Variables
No additional environment variables required. All timezone configuration is stored in the database.

### Dependencies
```txt
pytz==2023.3  # Added to requirements.txt
```

## Security Considerations

### 1. Input Validation
- Timezone names validated against pytz database
- Numeric settings have min/max bounds
- All inputs sanitized and validated

### 2. Access Control
- System settings require appropriate permissions
- API endpoints protected by authentication
- Audit trail for all setting changes

## Error Handling

### 1. Invalid Timezone
```json
{
  "detail": "Invalid timezone name"
}
```

### 2. Invalid Schedule Time
```json
{
  "detail": "Invalid schedule time: [error details]"
}
```

### 3. Validation Errors
```json
{
  "detail": "Invalid timeout value (must be 60-86400 seconds)"
}
```

## Testing

### 1. Timezone Conversion Tests
```python
# Test UTC to local conversion
utc_time = datetime.now(timezone.utc)
local_time = service.utc_to_local(utc_time)
assert local_time.tzinfo is not None

# Test local to UTC conversion
local_time = datetime.now()
utc_time = service.local_to_utc(local_time)
assert utc_time.tzinfo == timezone.utc
```

### 2. DST Transition Tests
```python
# Test DST detection
is_dst = service.is_dst_active()
assert isinstance(is_dst, bool)
```

## Future Enhancements

### 1. Multiple Timezone Support
- User-specific timezone preferences
- Per-job timezone settings
- Timezone-aware notifications

### 2. Advanced DST Rules
- Custom DST rules for specific regions
- Historical DST data
- DST transition notifications

### 3. Time Synchronization
- NTP server integration
- Time drift detection
- Automatic time correction

## Troubleshooting

### Common Issues

1. **Timezone not updating**
   - Check if timezone name is valid
   - Verify database connection
   - Check service logs

2. **DST not detected**
   - Ensure pytz is up to date
   - Check timezone database
   - Verify system time

3. **Time conversion errors**
   - Validate input datetime objects
   - Check timezone configuration
   - Review error logs

### Debug Information
```python
# Get system debug info
info = service.get_system_info()
print(f"Current timezone: {info['timezone']['current']}")
print(f"DST active: {info['timezone']['is_dst_active']}")
print(f"UTC offset: {info['timezone']['current_utc_offset']}")
```

## Conclusion

The system settings and timezone management system provides a robust foundation for accurate job scheduling in the ENABLEDRM platform. The implementation ensures that both users and the system have absolute clarity about when jobs will execute, with proper handling of timezone conversions and DST transitions.

This system is designed to be:
- **Accurate**: All times processed in UTC with proper conversions
- **Clear**: Users see times in their local timezone
- **Reliable**: Robust error handling and validation
- **Extensible**: Easy to add new settings and timezone features 