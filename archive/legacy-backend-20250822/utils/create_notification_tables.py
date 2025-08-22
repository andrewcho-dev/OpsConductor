#!/usr/bin/env python3
"""
Script to create notification database tables
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database.database import engine, Base
from app.models.notification_models import (
    NotificationTemplate, NotificationLog, AlertRule, AlertLog
)

def create_tables():
    """Create notification tables"""
    print("Creating notification tables...")
    
    # Import all models to register them
    from app.models import notification_models
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Notification tables created successfully!")

if __name__ == "__main__":
    create_tables()
