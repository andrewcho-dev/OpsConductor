#!/usr/bin/env python3
"""
Test script for Windows machine discovery improvements.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, '/home/enabledrm/backend')

from app.services.network_discovery_service import NetworkDiscoveryService, DiscoveryConfig

async def progress_callback(percent, total_ips, found_devices, message):
    """Progress callback for discovery updates."""
    print(f"Progress: {percent:.1f}% - {message}")

async def test_windows_discovery():
    """Test Windows machine discovery with enhanced settings."""
    print("🔍 Testing Enhanced Windows Discovery...")
    
    service = NetworkDiscoveryService()
    
    # Configuration optimized for Windows detection
    config = DiscoveryConfig(
        network_ranges=["192.168.50.0/24"],  # Your network range
        common_ports=[
            135, 139, 445,      # Windows core ports
            3389,               # RDP
            5985, 5986,         # WinRM
            80, 443,            # Web services
            22,                 # SSH (for Linux comparison)
            161                 # SNMP
        ],
        timeout=5.0,            # Longer timeout for Windows
        max_concurrent=25,      # Lower concurrency for better reliability
        enable_snmp=True,
        enable_service_detection=True,
        enable_hostname_resolution=True
    )
    
    print(f"🌐 Network range: {config.network_ranges}")
    print(f"🔌 Scanning ports: {config.common_ports}")
    print(f"⏱️  Timeout: {config.timeout}s")
    print(f"🔄 Max concurrent: {config.max_concurrent}")
    
    try:
        devices = await service.discover_network(config, progress_callback)
        
        print(f"\n✅ Discovery completed!")
        print(f"📊 Found {len(devices)} devices:")
        
        windows_devices = []
        other_devices = []
        
        for device in devices:
            print(f"\n📱 Device: {device.ip_address}")
            if device.hostname:
                print(f"   🏷️  Hostname: {device.hostname}")
            print(f"   🔌 Open ports: {device.open_ports}")
            print(f"   🏷️  Device type: {device.device_type}")
            print(f"   📊 Confidence: {device.confidence_score:.2f}")
            
            if device.services:
                print(f"   🔧 Services detected:")
                for port, service in device.services.items():
                    print(f"      Port {port}: {service}")
            
            if device.suggested_communication_methods:
                print(f"   💬 Suggested methods: {', '.join(device.suggested_communication_methods)}")
            
            # Categorize devices
            if 'windows' in device.device_type.lower():
                windows_devices.append(device)
            else:
                other_devices.append(device)
        
        print(f"\n📈 Summary:")
        print(f"   🪟 Windows devices: {len(windows_devices)}")
        print(f"   🐧 Other devices: {len(other_devices)}")
        
        if len(windows_devices) == 0:
            print(f"\n⚠️  No Windows devices found. This could mean:")
            print(f"   • Windows Firewall is blocking the scanned ports")
            print(f"   • No Windows machines are active on this network")
            print(f"   • Windows machines are using non-standard port configurations")
            print(f"   • Network segmentation is preventing access")
            
            print(f"\n💡 Troubleshooting suggestions:")
            print(f"   • Try scanning a smaller range (e.g., 192.168.50.1-192.168.50.10)")
            print(f"   • Increase timeout to 10+ seconds")
            print(f"   • Check if you can ping the Windows machines manually")
            print(f"   • Verify Windows machines have WinRM or RDP enabled")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_windows_discovery())