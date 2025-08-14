#!/usr/bin/env python3
"""
Test script to verify audit integration is working
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/home/opsconductor/backend')

from app.shared.infrastructure.cache import cache_service
from app.core.config import settings

async def test_audit_cache():
    """Test if audit events are being stored in cache"""
    print("🔍 Testing audit cache integration...")
    
    # Initialize cache service
    await cache_service.initialize()
    
    # Check if recent audit entries exist
    recent_entries = await cache_service.get("audit_recent_entries")
    print(f"📊 Recent audit entries in cache: {len(recent_entries) if recent_entries else 0}")
    
    if recent_entries:
        print("✅ Found audit entries in cache!")
        
        # Get the first few entries
        for i, entry_id in enumerate(recent_entries[:3]):
            entry = await cache_service.get(f"audit_entry:{entry_id}")
            if entry:
                print(f"📝 Entry {i+1}: {entry['event_type']} - {entry['action']} - {entry['timestamp']}")
            else:
                print(f"❌ Entry {i+1}: Could not retrieve entry {entry_id}")
    else:
        print("❌ No audit entries found in cache")
        
        # Check if there are any audit-related keys
        print("🔍 Checking for any audit keys in cache...")
        # This is a simplified check since we can't easily list all keys
        test_entry = await cache_service.get("audit_entry:test")
        print(f"Cache service is working: {test_entry is None}")

if __name__ == "__main__":
    asyncio.run(test_audit_cache())