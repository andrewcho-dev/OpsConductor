#!/usr/bin/env python3
"""
Test network discovery functionality
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/home/enabledrm/backend')

from app.services.network_discovery_service import NetworkDiscoveryService, DiscoveryConfig

async def test_discovery():
    """Test network discovery on 192.168.50.0/24"""
    print("Testing network discovery on 192.168.50.0/24...")
    
    service = NetworkDiscoveryService()
    
    # Create config for quick scan
    config = DiscoveryConfig(
        network_ranges=['192.168.50.0/24'],
        common_ports=[22, 80, 443, 135, 139, 445, 3389, 161],
        timeout=1.0,
        max_concurrent=50,
        enable_snmp=False,
        enable_service_detection=True,
        enable_hostname_resolution=True
    )
    
    print(f"Scanning network: {config.network_ranges}")
    print(f"Ports to check: {config.common_ports}")
    print(f"Timeout: {config.timeout}s")
    print(f"Max concurrent: {config.max_concurrent}")
    print("-" * 50)
    
    # Run discovery
    devices = await service.discover_network(config)
    
    print(f"\nDiscovery complete!")
    print(f"Found {len(devices)} devices:")
    
    for device in devices:
        print(f"\n  IP: {device.ip_address}")
        if device.hostname:
            print(f"  Hostname: {device.hostname}")
        print(f"  Open ports: {device.open_ports}")
        if device.device_type:
            print(f"  Device type: {device.device_type} (confidence: {device.confidence_score:.2f})")
        if device.suggested_communication_methods:
            print(f"  Suggested methods: {device.suggested_communication_methods}")

if __name__ == "__main__":
    asyncio.run(test_discovery())