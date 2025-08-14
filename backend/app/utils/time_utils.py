"""
Timezone and time utility functions for the OpsConductor platform.
This module provides centralized time handling for job scheduling and system operations.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import pytz
from sqlalchemy.orm import Session

from ..services.system_service import SystemService


class TimeUtils:
    """Utility class for timezone and time operations"""
    
    @staticmethod
    def get_system_service(db: Session) -> SystemService:
        """Get a system service instance for timezone operations"""
        return SystemService(db)
    
    @staticmethod
    def utc_to_local(utc_dt: datetime, db: Session) -> datetime:
        """
        Convert UTC datetime to local system timezone
        
        Args:
            utc_dt: UTC datetime object
            db: Database session
            
        Returns:
            Local datetime object
        """
        service = TimeUtils.get_system_service(db)
        return service.utc_to_local(utc_dt)
    
    @staticmethod
    def local_to_utc(local_dt: datetime, db: Session) -> datetime:
        """
        Convert local datetime to UTC
        
        Args:
            local_dt: Local datetime object
            db: Database session
            
        Returns:
            UTC datetime object
        """
        service = TimeUtils.get_system_service(db)
        return service.local_to_utc(local_dt)
    
    @staticmethod
    def format_local_time(utc_dt: datetime, db: Session, 
                         format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """
        Format UTC datetime as local time string
        
        Args:
            utc_dt: UTC datetime object
            db: Database session
            format_str: Format string for datetime
            
        Returns:
            Formatted local time string
        """
        service = TimeUtils.get_system_service(db)
        return service.utc_to_local_string(utc_dt, format_str)
    
    @staticmethod
    def get_current_time_info(db: Session) -> Dict[str, Any]:
        """
        Get current system time information
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with current time information
        """
        service = TimeUtils.get_system_service(db)
        now = datetime.now()
        
        return {
            "utc": now.isoformat(),
            "local": service.utc_to_local_string(now),
            "timezone": service.get_timezone(),
            "is_dst": service.is_dst_active(),
            "utc_offset": service.get_current_utc_offset()
        }
    
    @staticmethod
    def validate_job_schedule_time(local_time: datetime, db: Session) -> Dict[str, Any]:
        """
        Validate a job schedule time and provide conversion info
        
        Args:
            local_time: Local datetime for job scheduling
            db: Database session
            
        Returns:
            Dictionary with validation results and conversion info
        """
        service = TimeUtils.get_system_service(db)
        return service.validate_job_schedule_time(local_time)
    
    @staticmethod
    def get_timezone_display_name(db: Session) -> str:
        """
        Get human-readable timezone name
        
        Args:
            db: Database session
            
        Returns:
            Display name for current timezone
        """
        service = TimeUtils.get_system_service(db)
        return service.get_timezone_display_name()
    
    @staticmethod
    def is_dst_active(db: Session) -> bool:
        """
        Check if DST is currently active
        
        Args:
            db: Database session
            
        Returns:
            True if DST is active, False otherwise
        """
        service = TimeUtils.get_system_service(db)
        return service.is_dst_active()
    
    @staticmethod
    def get_available_timezones(db: Session) -> Dict[str, str]:
        """
        Get list of available timezones with display names
        
        Args:
            db: Database session
            
        Returns:
            Dictionary mapping timezone names to display names
        """
        service = TimeUtils.get_system_service(db)
        return service.get_available_timezones()


class JobScheduleTimeValidator:
    """Validator for job schedule times with timezone awareness"""
    
    @staticmethod
    def validate_and_convert(local_time: datetime, db: Session) -> Dict[str, Any]:
        """
        Validate a job schedule time and convert to UTC
        
        Args:
            local_time: Local datetime for job scheduling
            db: Database session
            
        Returns:
            Dictionary with validation results and UTC conversion
        """
        try:
            # Validate the time
            validation = TimeUtils.validate_job_schedule_time(local_time, db)
            
            if not validation['valid']:
                return {
                    'valid': False,
                    'error': validation['error'],
                    'local_time': None,
                    'utc_time': None
                }
            
            # Convert to UTC
            utc_time = TimeUtils.local_to_utc(local_time, db)
            
            return {
                'valid': True,
                'local_time': local_time.isoformat(),
                'utc_time': utc_time.isoformat(),
                'timezone': validation['timezone'],
                'is_dst': validation['is_dst'],
                'local_display': validation['local_display']
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Time validation failed: {str(e)}",
                'local_time': None,
                'utc_time': None
            }
    
    @staticmethod
    def format_schedule_time_for_display(utc_time: datetime, db: Session) -> str:
        """
        Format a UTC schedule time for display in local timezone
        
        Args:
            utc_time: UTC datetime to format
            db: Database session
            
        Returns:
            Formatted local time string
        """
        return TimeUtils.format_local_time(utc_time, db)
    
    @staticmethod
    def get_schedule_time_info(utc_time: datetime, db: Session) -> Dict[str, Any]:
        """
        Get comprehensive information about a schedule time
        
        Args:
            utc_time: UTC datetime
            db: Database session
            
        Returns:
            Dictionary with time information
        """
        service = TimeUtils.get_system_service(db)
        local_time = service.utc_to_local(utc_time)
        
        return {
            'utc_time': utc_time.isoformat(),
            'local_time': local_time.isoformat(),
            'local_display': service.utc_to_local_string(utc_time),
            'timezone': service.get_timezone(),
            'is_dst': service.is_dst_active(),
            'utc_offset': service.get_current_utc_offset()
        }


class TimezoneFormatter:
    """Utility for formatting timezone information"""
    
    @staticmethod
    def format_utc_offset(offset_seconds: int) -> str:
        """
        Format UTC offset in seconds to display string
        
        Args:
            offset_seconds: Offset in seconds
            
        Returns:
            Formatted offset string (e.g., "+05:30", "-08:00")
        """
        hours = int(offset_seconds / 3600)
        minutes = int((offset_seconds % 3600) / 60)
        sign = "+" if hours >= 0 else ""
        return f"{sign}{hours:03d}:{minutes:02d}"
    
    @staticmethod
    def get_timezone_display_name(tz_name: str) -> str:
        """
        Get display name for a timezone
        
        Args:
            tz_name: Timezone name
            
        Returns:
            Display name with UTC offset
        """
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(timezone.utc)
            offset = tz.utcoffset(now)
            offset_str = TimezoneFormatter.format_utc_offset(int(offset.total_seconds()))
            return f"{tz_name} (UTC{offset_str})"
        except pytz.UnknownTimeZoneError:
            return f"{tz_name} (Unknown)"
    
    @staticmethod
    def get_current_timezone_info() -> Dict[str, Any]:
        """
        Get current timezone information without database dependency
        
        Returns:
            Dictionary with current timezone info
        """
        # This is a fallback method that doesn't require database access
        # It uses system default timezone
        try:
            import time
            tz_name = time.tzname[time.daylight]
            tz = pytz.timezone(tz_name)
            now = datetime.now(timezone.utc)
            offset = tz.utcoffset(now)
            
            return {
                'timezone': tz_name,
                'display_name': TimezoneFormatter.get_timezone_display_name(tz_name),
                'is_dst_active': bool(tz.dst(now)),
                'utc_offset': TimezoneFormatter.format_utc_offset(int(offset.total_seconds()))
            }
        except Exception:
            return {
                'timezone': 'UTC',
                'display_name': 'UTC (UTC+00:00)',
                'is_dst_active': False,
                'utc_offset': '+00:00'
            } 