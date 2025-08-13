#!/usr/bin/env python3
"""
Fast test script for improved Windows discovery performance.
"""
import asyncio
import sys
import time

# Add the backend directory to the Python path
sys.path.insert(0, '/home/enabledrm/backend')

from app.services.network_discovery_service import NetworkDiscoveryService, DiscoveryConfig

async def progress_callback(percent, total_ips, found_devices, message):
    """Progress callback for discovery updates."""
    print(f"Progress: {percent:.1f}% - {message}")

async def test_fast_discovery():
    """Test fast Windows discovery with optimized settings."""
    print("🚀 Testing FAST Windows Discovery...")
    
    service = NetworkDiscoveryService()
    
    # Optimized configuration for speed
    config = DiscoveryConfig(
        network_ranges=["192.168.50.0/24"],
        common_ports=[
            135, 139, 445,      # Windows core ports
            3389,               # RDP
            5985, 5986,         # WinRM
            22,                 # SSH
            80, 443,            # Web
            161                 # SNMP
        ],
        timeout=2.0,            # Faster timeout
        max_concurrent=200,     # Higher concurrency
        enable_snmp=True,       # Now available!
        enable_service_detection=True,
        enable_hostname_resolution=True
    )
    
    print(f"🌐 Network: {config.network_ranges[0]}")
    print(f"⚡ Optimized for speed: {config.timeout}s timeout, {config.max_concurrent} concurrent")
    print(f"🔌 Key ports: {config.common_ports}")
    
    start_time = time.time()
    
    try:
        devices = await service.discover_network(config, progress_callback)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎯 RESULTS:")
        print(f"⏱️  Total time: {duration:.1f} seconds")
        print(f"📊 Found {len(devices)} devices")
        print(f"🚀 Speed: {254/duration:.1f} IPs/second")
        
        windows_count = sum(1 for d in devices if 'windows' in d.device_type.lower())
        print(f"🪟 Windows devices: {windows_count}")
        
        if duration < 30:
            print("✅ EXCELLENT: Fast discovery working!")
        elif duration < 60:
            print("⚠️  GOOD: Reasonable speed")
        else:
            print("❌ SLOW: Still needs optimization")
            
        # Show Windows devices found
        if windows_count > 0:
            print(f"\n🪟 Windows Devices Found:")
            for device in devices:
                if 'windows' in device.device_type.lower():
                    ports_str = ', '.join(map(str, device.open_ports[:5]))
                    if len(device.open_ports) > 5:
                        ports_str += f" (+{len(device.open_ports)-5} more)"
                    print(f"   • {device.ip_address}: {device.device_type} - ports: {ports_str}")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fast_discovery())