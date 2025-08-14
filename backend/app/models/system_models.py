from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
import pytz
from typing import Dict, Any

Base = declarative_base()


class SystemSetting(Base):
    """System settings model for storing configuration data"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    def __repr__(self):
        return (f"<SystemSetting(key='{self.setting_key}', "
                f"value={self.setting_value})>")


class TimezoneManager:
    """Manages timezone and DST configuration for the system"""
    
    @staticmethod
    def get_system_timezone() -> str:
        """Get the configured system timezone"""
        # This will be implemented in the service layer
        # Default to UTC if not configured
        return "UTC"
    
    @staticmethod
    def get_system_tzinfo() -> timezone:
        """Get the timezone object for the system"""
        tz_name = TimezoneManager.get_system_timezone()
        try:
            return pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            return timezone.utc
    
    @staticmethod
    def get_dst_rules() -> Dict[str, Any]:
        """Get DST rules configuration"""
        # This will be implemented in the service layer
        # Default empty rules
        return {}
    
    @staticmethod
    def utc_to_local(utc_dt: datetime) -> datetime:
        """Convert UTC datetime to local system timezone"""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        system_tz = TimezoneManager.get_system_tzinfo()
        return utc_dt.astimezone(system_tz)
    
    @staticmethod
    def local_to_utc(local_dt: datetime) -> datetime:
        """Convert local datetime to UTC"""
        system_tz = TimezoneManager.get_system_tzinfo()
        
        if local_dt.tzinfo is None:
            # Assume it's in system timezone
            if hasattr(system_tz, 'localize'):
                local_dt = system_tz.localize(local_dt)
            else:
                # For timezone objects that don't have localize
                local_dt = local_dt.replace(tzinfo=system_tz)
        
        return local_dt.astimezone(timezone.utc)
    
    @staticmethod
    def format_local_time(utc_dt: datetime,
                         format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """Format UTC datetime as local time string"""
        local_dt = TimezoneManager.utc_to_local(utc_dt)
        return local_dt.strftime(format_str)
    
    @staticmethod
    def get_timezone_display_name() -> str:
        """Get human-readable timezone name"""
        tz_name = TimezoneManager.get_system_timezone()
        try:
            tz = pytz.timezone(tz_name)
            # Get current offset
            now = datetime.now(timezone.utc)
            offset = tz.utcoffset(now)
            offset_hours = int(offset.total_seconds() / 3600)
            offset_minutes = int((offset.total_seconds() % 3600) / 60)
            offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
            return f"{tz_name} (UTC{offset_str})"
        except pytz.UnknownTimeZoneError:
            return f"{tz_name} (Unknown)"
    
    @staticmethod
    def is_dst_active() -> bool:
        """Check if DST is currently active in the system timezone"""
        try:
            tz = TimezoneManager.get_system_tzinfo()
            now = datetime.now(timezone.utc)
            return bool(tz.dst(now))
        except Exception:
            return False
    
    @staticmethod
    def get_available_timezones() -> Dict[str, str]:
        """Get list of available timezones with display names"""
        timezones = {}
        for tz_name in pytz.all_timezones:
            try:
                tz = pytz.timezone(tz_name)
                now = datetime.now(timezone.utc)
                offset = tz.utcoffset(now)
                offset_hours = int(offset.total_seconds() / 3600)
                offset_minutes = int((offset.total_seconds() % 3600) / 60)
                offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
                display_name = f"{tz_name} (UTC{offset_str})"
                timezones[tz_name] = display_name
            except Exception:
                continue
        return timezones 