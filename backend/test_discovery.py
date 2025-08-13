#!/usr/bin/env python3
"""
Quick test script for the network discovery service.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, '/home/enabledrm/backend')

from app.services.network_discovery_service import NetworkDiscoveryService, DiscoveryConfig


async def test_discovery():
    """Test the network discovery service."""
    print("🔍 Testing Network Discovery Service...")
    
    service = NetworkDiscoveryService()
    
    # Test with a small local network range
    config = DiscoveryConfig(
        network_ranges=['127.0.0.1/32'],  # Just localhost
        common_ports=[22, 80, 443, 8000, 8080],
        timeout=2.0,
        max_concurrent=10,
        enable_snmp=False,  # Disable SNMP for quick test
        enable_service_detection=True,
        enable_hostname_resolution=True
    )
    
    print(f"📡 Scanning network range: {config.network_ranges}")
    print(f"🔌 Scanning ports: {config.common_ports}")
    
    try:
        devices = await service.discover_network(config)
        
        print(f"\n✅ Discovery completed!")
        print(f"📊 Found {len(devices)} devices:")
        
        for device in devices:
            print(f"\n🖥️  Device: {device.ip_address}")
            if device.hostname:
                print(f"   Hostname: {device.hostname}")
            print(f"   Open Ports: {device.open_ports}")
            print(f"   Device Type: {device.device_type} (confidence: {device.confidence_score:.2f})")
            print(f"   Suggested Methods: {device.suggested_communication_methods}")
            
            if device.services:
                print("   Services:")
                for port, service_info in device.services.items():
                    print(f"     Port {port}: {service_info.get('service', 'unknown')} - {service_info.get('banner', 'No banner')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Discovery failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_discovery())
    if success:
        print("\n🎉 Network discovery test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Network discovery test failed!")
        sys.exit(1)