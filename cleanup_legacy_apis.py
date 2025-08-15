#!/usr/bin/env python3
"""
Legacy API Cleanup Script for OpsConductor
Identifies and removes legacy API files that have been replaced by enhanced versions

LEGACY APIs TO REMOVE:
- All non-enhanced API files that have enhanced counterparts
- Duplicate files in wrong directories
- Outdated API implementations
"""

import os
import sys
from pathlib import Path

def identify_legacy_apis():
    """Identify legacy API files that should be removed"""
    
    print("🧹 OPSCONDUCTOR LEGACY API CLEANUP")
    print("=" * 60)
    
    # Define the API directory
    api_dir = Path("/home/enabledrm/backend/app/api")
    
    # Legacy files to remove (have enhanced counterparts)
    legacy_files = [
        # v1 Legacy APIs (replaced by v2 enhanced)
        "v1/audit.py",                    # → v2/audit_enhanced.py
        "v1/websocket.py",               # → v2/websocket_enhanced.py  
        "v1/device_types.py",            # → v2/device_types_enhanced.py
        
        # v2 Legacy APIs (replaced by v2 enhanced)
        "v2/jobs.py",                    # → v2/jobs_enhanced.py
        "v2/metrics.py",                 # → v2/metrics_enhanced.py
        "v2/system.py",                  # → v2/system_enhanced.py
        "v2/discovery.py",               # → v2/discovery_enhanced.py
        "v2/health.py",                  # → v2/health_enhanced.py
        "v2/notifications.py",           # → v2/notifications_enhanced.py
        "v2/templates.py",               # → v2/templates_enhanced.py
        "v2/device_types.py",            # → v2/device_types_enhanced.py
        
        # Duplicate enhanced files in wrong locations
        "v1/audit_enhanced.py",          # → v2/audit_enhanced.py (moved)
        "v1/websocket_enhanced.py",      # → v2/websocket_enhanced.py (moved)
        "websocket_enhanced.py",         # → v2/websocket_enhanced.py (moved)
    ]
    
    print("📋 LEGACY FILES IDENTIFIED FOR REMOVAL:")
    print("-" * 60)
    
    files_to_remove = []
    files_not_found = []
    
    for legacy_file in legacy_files:
        file_path = api_dir / legacy_file
        if file_path.exists():
            files_to_remove.append(file_path)
            print(f"🗑️  {legacy_file}")
        else:
            files_not_found.append(legacy_file)
            print(f"❌ {legacy_file} (not found)")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"✅ Files to remove: {len(files_to_remove)}")
    print(f"❌ Files not found: {len(files_not_found)}")
    
    # Show enhanced files that will remain
    print(f"\n🚀 ENHANCED FILES REMAINING:")
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
    
    for enhanced_file in enhanced_files:
        file_path = api_dir / enhanced_file
        if file_path.exists():
            print(f"✅ {enhanced_file}")
        else:
            print(f"❌ {enhanced_file} (MISSING!)")
    
    return files_to_remove

def remove_legacy_files(files_to_remove, dry_run=True):
    """Remove legacy API files"""
    
    print(f"\n🗑️  LEGACY FILE REMOVAL ({'DRY RUN' if dry_run else 'ACTUAL'})")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be actually removed")
        print("📋 Files that WOULD be removed:")
        
        for file_path in files_to_remove:
            print(f"   🗑️  {file_path}")
            
        print(f"\n💡 To actually remove files, run with dry_run=False")
        
    else:
        print("⚠️  ACTUAL REMOVAL MODE - Files will be permanently deleted")
        
        removed_count = 0
        failed_count = 0
        
        for file_path in files_to_remove:
            try:
                file_path.unlink()
                print(f"✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")
                failed_count += 1
        
        print(f"\n📊 REMOVAL SUMMARY:")
        print(f"✅ Successfully removed: {removed_count}")
        print(f"❌ Failed to remove: {failed_count}")
    
    return len(files_to_remove)

def verify_enhanced_apis():
    """Verify all enhanced APIs are in place"""
    
    print(f"\n🔍 ENHANCED API VERIFICATION")
    print("=" * 60)
    
    api_dir = Path("/home/enabledrm/backend/app/api")
    
    required_enhanced_apis = [
        ("v2/audit_enhanced.py", "Audit Management Enhanced v2"),
        ("v2/websocket_enhanced.py", "WebSocket Management Enhanced v2"),
        ("v2/jobs_enhanced.py", "Jobs Management Enhanced v2"),
        ("v2/metrics_enhanced.py", "Metrics & Analytics Enhanced v2"),
        ("v2/system_enhanced.py", "System Administration Enhanced v2"),
        ("v2/discovery_enhanced.py", "Network Discovery Enhanced v2"),
        ("v2/health_enhanced.py", "Health & Monitoring Enhanced v2"),
        ("v2/notifications_enhanced.py", "Notifications & Alerts Enhanced v2"),
        ("v2/templates_enhanced.py", "Templates Management Enhanced v2"),
        ("v2/device_types_enhanced.py", "Device Types Management Enhanced v2")
    ]
    
    all_present = True
    
    for api_file, description in required_enhanced_apis:
        file_path = api_dir / api_file
        if file_path.exists():
            print(f"✅ {api_file} - {description}")
        else:
            print(f"❌ {api_file} - {description} (MISSING!)")
            all_present = False
    
    print(f"\n📊 VERIFICATION RESULT:")
    if all_present:
        print("🏆 ALL ENHANCED APIS PRESENT - READY FOR CLEANUP!")
    else:
        print("⚠️  SOME ENHANCED APIS MISSING - DO NOT CLEANUP YET!")
    
    return all_present

def main():
    """Main cleanup function"""
    
    print("🚀 Starting OpsConductor Legacy API Cleanup...")
    
    # Step 1: Verify enhanced APIs are in place
    if not verify_enhanced_apis():
        print("\n❌ CLEANUP ABORTED - Enhanced APIs missing!")
        return False
    
    # Step 2: Identify legacy files
    files_to_remove = identify_legacy_apis()
    
    if not files_to_remove:
        print("\n🎉 NO LEGACY FILES FOUND - CLEANUP ALREADY COMPLETE!")
        return True
    
    # Step 3: Show what would be removed (dry run)
    remove_legacy_files(files_to_remove, dry_run=True)
    
    print(f"\n🎯 CLEANUP READY!")
    print("📋 To perform actual cleanup:")
    print("   1. Review the files listed above")
    print("   2. Ensure all enhanced APIs are working")
    print("   3. Run: remove_legacy_files(files_to_remove, dry_run=False)")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎉 LEGACY API CLEANUP ANALYSIS COMPLETE!")
        sys.exit(0)
    else:
        print(f"\n❌ LEGACY API CLEANUP ANALYSIS FAILED!")
        sys.exit(1)