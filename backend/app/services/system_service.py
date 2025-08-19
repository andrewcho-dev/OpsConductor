from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import pytz
import psutil

from ..models.system_models import SystemSetting


class SystemService:
    """Service for managing system settings and configuration"""
    
    def __init__(self, db: Session):
        self.db = db
        self._timezone_cache = None
        self._dst_rules_cache = None
    
    def get_setting(self, key: str) -> Optional[Any]:
        """Get a system setting by key"""
        try:
            stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
            result = self.db.execute(stmt).scalar_one_or_none()
            return result.setting_value if result else None
        except Exception as e:
            print(f"Error getting setting {key}: {e}")
            return None
    
    def set_setting(self, key: str, value: Any, 
                   description: str = None) -> SystemSetting:
        """Set a system setting"""
        try:
            stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.setting_value = value
                if description:
                    existing.description = description
                existing.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                return existing
            else:
                new_setting = SystemSetting(
                    setting_key=key,
                    setting_value=value,
                    description=description
                )
                self.db.add(new_setting)
                self.db.commit()
                self.db.refresh(new_setting)
                return new_setting
        except Exception as e:
            print(f"Error setting {key}: {e}")
            self.db.rollback()
            raise
    
    def get_all_settings(self) -> List[SystemSetting]:
        """Get all system settings"""
        stmt = select(SystemSetting).order_by(SystemSetting.setting_key)
        return list(self.db.execute(stmt).scalars().all())
    
    def get_timezone(self) -> str:
        """Get the configured system timezone"""
        if self._timezone_cache is None:
            timezone_setting = self.get_setting('timezone')
            self._timezone_cache = timezone_setting if timezone_setting else "UTC"
        return self._timezone_cache
    
    def set_timezone(self, timezone_name: str) -> bool:
        """Set the system timezone"""
        try:
            # Validate timezone
            pytz.timezone(timezone_name)
            
            # Update setting
            self.set_setting('timezone', timezone_name, 
                           'System timezone configuration')
            
            # Clear cache
            self._timezone_cache = timezone_name
            
            return True
        except pytz.UnknownTimeZoneError:
            return False
    
    def get_dst_rules(self) -> Dict[str, Any]:
        """Get DST rules configuration"""
        if self._dst_rules_cache is None:
            dst_rules = self.get_setting('dst_rules')
            self._dst_rules_cache = dst_rules if dst_rules else {}
        return self._dst_rules_cache
    
    def set_dst_rules(self, rules: Dict[str, Any]) -> bool:
        """Set DST rules configuration"""
        try:
            # Validate rules structure
            if not isinstance(rules, dict):
                return False
            
            # Update setting
            self.set_setting('dst_rules', rules, 'Daylight saving time rules')
            
            # Clear cache
            self._dst_rules_cache = rules
            
            return True
        except Exception:
            return False
    
    def get_session_timeout(self) -> int:
        """Get user session timeout in seconds"""
        timeout = self.get_setting('session_timeout')
        return int(timeout) if timeout else 28800  # Default 8 hours
    
    def set_session_timeout(self, timeout_seconds: int) -> bool:
        """Set user session timeout in seconds"""
        try:
            if timeout_seconds < 60 or timeout_seconds > 86400:  # 1 min to 24 hours
                return False
            
            self.set_setting('session_timeout', timeout_seconds, 
                           'User session timeout in seconds')
            return True
        except Exception:
            return False
    
    def get_inactivity_timeout(self) -> int:
        """Get user inactivity timeout in minutes"""
        timeout = self.get_setting('inactivity_timeout_minutes')
        return int(timeout) if timeout else 60  # Default 60 minutes
    
    def set_inactivity_timeout(self, timeout_minutes: int) -> bool:
        """Set user inactivity timeout in minutes"""
        try:
            if timeout_minutes < 5 or timeout_minutes > 480:  # 5 min to 8 hours
                return False
            
            self.set_setting('inactivity_timeout_minutes', timeout_minutes, 
                           'User inactivity timeout in minutes for activity-based sessions')
            return True
        except Exception:
            return False
    
    def get_warning_time(self) -> int:
        """Get warning time before timeout in minutes"""
        warning_time = self.get_setting('warning_time_minutes')
        return int(warning_time) if warning_time else 2  # Default 2 minutes
    
    def set_warning_time(self, warning_minutes: int) -> bool:
        """Set warning time before timeout in minutes"""
        try:
            if warning_minutes < 1 or warning_minutes > 10:  # 1-10 minutes
                return False
            
            self.set_setting('warning_time_minutes', warning_minutes, 
                           'Warning time in minutes before session timeout')
            return True
        except Exception:
            return False
    
    def get_max_concurrent_jobs(self) -> int:
        """Get maximum concurrent job executions"""
        max_jobs = self.get_setting('max_concurrent_jobs')
        return int(max_jobs) if max_jobs else 50
    
    def set_max_concurrent_jobs(self, max_jobs: int) -> bool:
        """Set maximum concurrent job executions"""
        try:
            if max_jobs < 1 or max_jobs > 1000:
                return False
            
            self.set_setting('max_concurrent_jobs', max_jobs,
                           'Maximum concurrent job executions')
            return True
        except Exception:
            return False
    
    def get_log_retention_days(self) -> int:
        """Get log retention period in days"""
        retention = self.get_setting('log_retention_days')
        return int(retention) if retention else 30
    
    def set_log_retention_days(self, days: int) -> bool:
        """Set log retention period in days"""
        try:
            if days < 1 or days > 3650:  # 1 day to 10 years
                return False
            
            self.set_setting('log_retention_days', days,
                           'How long to keep logs in days')
            return True
        except Exception:
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            'timezone': {
                'current': self.get_timezone(),
                'display_name': self.get_timezone_display_name(),
                'is_dst_active': self.is_dst_active(),
                'current_utc_offset': self.get_current_utc_offset()
            },
            'session_timeout': self.get_session_timeout(),
            'inactivity_timeout_minutes': self.get_inactivity_timeout(),
            'warning_time_minutes': self.get_warning_time(),
            'max_concurrent_jobs': self.get_max_concurrent_jobs(),
            'log_retention_days': self.get_log_retention_days(),
            'uptime': self.get_system_uptime(),
            'system_time': {
                'utc': datetime.now(timezone.utc).isoformat(),
                'local': self.utc_to_local_string(datetime.now(timezone.utc))
            }
        }
    
    def get_system_uptime(self) -> str:
        """Get system uptime as a human-readable string"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "Unknown"
    
    def get_timezone_display_name(self) -> str:
        """Get human-readable timezone name"""
        tz_name = self.get_timezone()
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now()  # Use naive datetime
            offset = tz.utcoffset(now)
            offset_hours = int(offset.total_seconds() / 3600)
            offset_minutes = int((offset.total_seconds() % 3600) / 60)
            offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
            return f"{tz_name} (UTC{offset_str})"
        except pytz.UnknownTimeZoneError:
            return f"{tz_name} (Unknown)"
    
    def get_current_utc_offset(self) -> str:
        """Get current UTC offset as string"""
        tz_name = self.get_timezone()
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now()  # Use naive datetime
            offset = tz.utcoffset(now)
            offset_hours = int(offset.total_seconds() / 3600)
            offset_minutes = int((offset.total_seconds() % 3600) / 60)
            return f"{offset_hours:+03d}:{offset_minutes:02d}"
        except pytz.UnknownTimeZoneError:
            return "+00:00"
    
    def is_dst_active(self) -> bool:
        """Check if DST is currently active"""
        try:
            tz_name = self.get_timezone()
            tz = pytz.timezone(tz_name)
            now = datetime.now()  # Use naive datetime
            return bool(tz.dst(now))
        except Exception:
            return False
    
    def utc_to_local(self, utc_dt: datetime) -> datetime:
        """Convert UTC datetime to local system timezone"""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        tz_name = self.get_timezone()
        try:
            tz = pytz.timezone(tz_name)
            return utc_dt.astimezone(tz)
        except pytz.UnknownTimeZoneError:
            return utc_dt.astimezone(timezone.utc)
    
    def local_to_utc(self, local_dt: datetime) -> datetime:
        """Convert local datetime to UTC"""
        tz_name = self.get_timezone()
        try:
            tz = pytz.timezone(tz_name)
            
            if local_dt.tzinfo is None:
                # Assume it's in system timezone
                if hasattr(tz, 'localize'):
                    local_dt = tz.localize(local_dt)
                else:
                    local_dt = local_dt.replace(tzinfo=tz)
            
            return local_dt.astimezone(timezone.utc)
        except pytz.UnknownTimeZoneError:
            if local_dt.tzinfo is None:
                local_dt = local_dt.replace(tzinfo=timezone.utc)
            return local_dt
    
    def utc_to_local_string(self, utc_dt: datetime,
                           format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """Convert UTC datetime to local time string"""
        local_dt = self.utc_to_local(utc_dt)
        return local_dt.strftime(format_str)
    
    def get_available_timezones(self) -> Dict[str, str]:
        """Get list of available timezones with display names"""
        timezones = {}
        
        # Common timezone abbreviations and their full names
        common_abbreviations = {
            'UTC': 'UTC (Coordinated Universal Time)',
            'GMT': 'GMT (Greenwich Mean Time)',
            'EST': 'EST (Eastern Standard Time)',
            'CST': 'CST (Central Standard Time)',
            'MST': 'MST (Mountain Standard Time)',
            'PST': 'PST (Pacific Standard Time)',
            'EDT': 'EDT (Eastern Daylight Time)',
            'CDT': 'CDT (Central Daylight Time)',
            'MDT': 'MDT (Mountain Daylight Time)',
            'PDT': 'PDT (Pacific Daylight Time)',
        }
        
        # Add common abbreviations first
        for tz_name in common_abbreviations:
            try:
                tz = pytz.timezone(tz_name)
                now = datetime.now()  # Use naive datetime
                offset = tz.utcoffset(now)
                offset_hours = int(offset.total_seconds() / 3600)
                offset_minutes = int((offset.total_seconds() % 3600) / 60)
                offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
                display_name = f"{common_abbreviations[tz_name]} (UTC{offset_str})"
                timezones[tz_name] = display_name
            except Exception:
                continue
        
        # Add major city timezones (more comprehensive list)
        major_cities = [
            'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
            'America/Toronto', 'America/Vancouver', 'America/Montreal', 'America/Edmonton',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome', 'Europe/Madrid',
            'Europe/Amsterdam', 'Europe/Brussels', 'Europe/Vienna', 'Europe/Zurich',
            'Europe/Stockholm', 'Europe/Oslo', 'Europe/Copenhagen', 'Europe/Helsinki',
            'Europe/Warsaw', 'Europe/Prague', 'Europe/Budapest', 'Europe/Bucharest',
            'Europe/Sofia', 'Europe/Athens', 'Europe/Istanbul', 'Europe/Moscow',
            'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Seoul', 'Asia/Singapore', 'Asia/Hong_Kong',
            'Asia/Bangkok', 'Asia/Jakarta', 'Asia/Manila', 'Asia/Kuala_Lumpur',
            'Asia/Dubai', 'Asia/Kolkata', 'Asia/Karachi', 'Asia/Dhaka', 'Asia/Tashkent',
            'Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane', 'Australia/Perth',
            'Australia/Adelaide', 'Australia/Darwin', 'Australia/Hobart',
            'Pacific/Auckland', 'Pacific/Fiji', 'Pacific/Guam', 'Pacific/Honolulu',
            'Africa/Cairo', 'Africa/Johannesburg', 'Africa/Lagos', 'Africa/Nairobi',
            'Africa/Casablanca', 'Africa/Algiers', 'Africa/Tunis', 'Africa/Luanda',
            'America/Sao_Paulo', 'America/Buenos_Aires', 'America/Santiago', 'America/Lima',
            'America/Bogota', 'America/Caracas', 'America/Mexico_City', 'America/Panama',
            'America/Jamaica', 'America/Havana', 'America/Puerto_Rico', 'America/Guatemala'
        ]
        
        # Add major city timezones
        for tz_name in major_cities:
            if tz_name not in timezones:  # Skip if already added as abbreviation
                try:
                    tz = pytz.timezone(tz_name)
                    now = datetime.now()  # Use naive datetime
                    offset = tz.utcoffset(now)
                    offset_hours = int(offset.total_seconds() / 3600)
                    offset_minutes = int((offset.total_seconds() % 3600) / 60)
                    offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
                    
                    # Create user-friendly display name
                    if '/' in tz_name:
                        # Convert "Continent/City" to "City, Continent"
                        parts = tz_name.split('/')
                        if len(parts) >= 2:
                            continent = parts[0].replace('_', ' ')
                            city = parts[-1].replace('_', ' ')
                            display_name = f"{city}, {continent} (UTC{offset_str})"
                        else:
                            display_name = f"{tz_name} (UTC{offset_str})"
                    else:
                        display_name = f"{tz_name} (UTC{offset_str})"
                    
                    timezones[tz_name] = display_name
                except Exception:
                    continue
        
        # Add additional timezones from pytz.all_timezones (filtered)
        for tz_name in pytz.all_timezones:
            # Skip if already added
            if tz_name in timezones:
                continue
                
            # Skip non-user-friendly timezones
            if (tz_name.startswith('Etc/') or 
                tz_name.startswith('GMT') or 
                tz_name.startswith('UTC') or
                tz_name.startswith('SystemV/') or
                tz_name.startswith('US/')):
                continue
                
            # Only include timezones with continent/city format
            if '/' in tz_name and not tz_name.startswith('Etc/'):
                try:
                    tz = pytz.timezone(tz_name)
                    now = datetime.now()  # Use naive datetime
                    offset = tz.utcoffset(now)
                    offset_hours = int(offset.total_seconds() / 3600)
                    offset_minutes = int((offset.total_seconds() % 3600) / 60)
                    offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
                    
                    # Create user-friendly display name
                    parts = tz_name.split('/')
                    if len(parts) >= 2:
                        continent = parts[0].replace('_', ' ')
                        city = parts[-1].replace('_', ' ')
                        display_name = f"{city}, {continent} (UTC{offset_str})"
                    else:
                        display_name = f"{tz_name} (UTC{offset_str})"
                    
                    timezones[tz_name] = display_name
                except Exception:
                    continue
        
        # Sort by display name for better user experience
        return dict(sorted(timezones.items(), key=lambda x: x[1]))
    
    def validate_job_schedule_time(self, local_time: datetime) -> Dict[str, Any]:
        """Validate a job schedule time and provide conversion info"""
        try:
            utc_time = self.local_to_utc(local_time)
            local_display = self.utc_to_local_string(utc_time)
            
            return {
                'valid': True,
                'local_time': local_time.isoformat(),
                'utc_time': utc_time.isoformat(),
                'local_display': local_display,
                'timezone': self.get_timezone(),
                'is_dst': self.is_dst_active()
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            } 