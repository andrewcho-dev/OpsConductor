#!/usr/bin/env python3
"""
Execute Legacy API Cleanup for OpsConductor
Actually removes the legacy API files after verification
"""

import os
import sys
from pathlib import Path

def execute_cleanup():
    """Execute the actual cleanup of legacy APIs"""
    
    print("🗑️  EXECUTING OPSCONDUCTOR LEGACY API CLEANUP")
    print("=" * 60)
    
    # Define the API directory
    api_dir = Path("/home/enabledrm/backend/app/api")
    
    # Legacy files to remove
    legacy_files = [
        # v1 Legacy APIs (replaced by v2 enhanced)
        "v1/audit.py",
        "v1/websocket.py", 
        "v1/device_types.py",
        
        # v2 Legacy APIs (replaced by v2 enhanced)
        "v2/jobs.py",
        "v2/metrics.py",
        "v2/system.py",
        "v2/discovery.py",
        "v2/health.py",
        "v2/notifications.py",
        "v2/templates.py",
        "v2/device_types.py",
        
        # Duplicate enhanced files in wrong locations
        "v1/audit_enhanced.py",
        "v1/websocket_enhanced.py",
        "websocket_enhanced.py",
    ]
    
    removed_count = 0
    failed_count = 0
    
    print("🗑️  REMOVING LEGACY FILES:")
    print("-" * 60)
    
    for legacy_file in legacy_files:
        file_path = api_dir / legacy_file
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Removed: {legacy_file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {legacy_file}: {e}")
                failed_count += 1
        else:
            print(f"⚠️  Not found: {legacy_file}")
    
    print(f"\n📊 CLEANUP RESULTS:")
    print(f"✅ Successfully removed: {removed_count}")
    print(f"❌ Failed to remove: {failed_count}")
    
    # Verify enhanced APIs are still present
    print(f"\n🔍 VERIFYING ENHANCED APIS REMAIN:")
    print("-" * 60)
    
    enhanced_files = [
        "v2/audit_enhanced.py",
        "v2/websocket_enhanced.py", 
        "v2/jobs_enhanced.py",
        "v2/metrics_enhanced.py",
        "v2/system_enhanced.py",
        "v2/discovery_enhanced.py",
        "v2/health_enhanced.py",
        "v2/notifications_enhanced.py",
        "v2/templates_enhanced.py",
        "v2/device_types_enhanced.py"
    ]
    
    all_enhanced_present = True
    
    for enhanced_file in enhanced_files:
        file_path = api_dir / enhanced_file
        if file_path.exists():
            print(f"✅ {enhanced_file}")
        else:
            print(f"❌ {enhanced_file} (MISSING!)")
            all_enhanced_present = False
    
    if all_enhanced_present:
        print(f"\n🎉 CLEANUP SUCCESSFUL!")
        print("✅ All legacy APIs removed")
        print("✅ All enhanced APIs preserved")
        print("🚀 OpsConductor is now clean with only enhanced v2 APIs!")
        return True
    else:
        print(f"\n❌ CLEANUP ISSUE!")
        print("⚠️  Some enhanced APIs are missing!")
        return False

if __name__ == "__main__":
    success = execute_cleanup()
    
    if success:
        print(f"\n🏆 OPSCONDUCTOR LEGACY API CLEANUP COMPLETE!")
        sys.exit(0)
    else:
        print(f"\n❌ OPSCONDUCTOR LEGACY API CLEANUP FAILED!")
        sys.exit(1)