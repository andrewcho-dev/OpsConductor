"""
System Models
Database models for system settings and configuration
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base
import pytz
from datetime import datetime
from typing import Optional, Dict, Any


class SystemSetting(Base):
    """System configuration settings"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    is_readonly = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"


class TimezoneManager:
    """Utility class for timezone management"""
    
    @staticmethod
    def get_available_timezones():
        """Get list of available timezones"""
        return list(pytz.all_timezones)
    
    @staticmethod
    def get_common_timezones():
        """Get list of common timezones"""
        return [
            'UTC',
            'US/Eastern',
            'US/Central', 
            'US/Mountain',
            'US/Pacific',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Asia/Tokyo',
            'Asia/Shanghai',
            'Australia/Sydney'
        ]
    
    @staticmethod
    def convert_timezone(dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime from one timezone to another"""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = pytz.UTC.localize(dt)
        elif dt.tzinfo != pytz.UTC:
            # Convert to UTC first
            dt = dt.astimezone(pytz.UTC)
        
        # Convert to target timezone
        target_tz = pytz.timezone(to_tz)
        return dt.astimezone(target_tz)
    
    @staticmethod
    def get_system_timezone() -> str:
        """Get the system's default timezone"""
        return 'UTC'  # Default to UTC for consistency
    
    @staticmethod
    def validate_timezone(timezone_str: str) -> bool:
        """Validate if timezone string is valid"""
        try:
            pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False