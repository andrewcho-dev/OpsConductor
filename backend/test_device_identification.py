#!/usr/bin/env python3
"""
Test script for the enhanced device identification system
"""

import sys
import os
sys.path.append('/home/enabledrm/backend')

from app.services.discovery_management_service import DiscoveryManagementService

def test_device_identification():
    """Test the enhanced device identification with mock data"""
    
    # Create service instance (without DB for testing)
    service = DiscoveryManagementService(None)
    
    print("🧪 Testing Enhanced Device Identification System")
    print("=" * 60)
    
    # Test cases with different device scenarios
    test_cases = [
        {
            "name": "MySQL Database Server",
            "host_ip": "192.168.1.100",
            "open_ports": [22, 80, 443, 3306],
            "hostname": "db-mysql-01",
            "service_info": {22: "OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"},
            "mac_info": {"mac": "00:50:56:12:34:56", "vendor": "VMware"}
        },
        {
            "name": "Cisco Network Device",
            "host_ip": "192.168.1.1",
            "open_ports": [22, 23, 80, 161],
            "hostname": "cisco-switch-01",
            "service_info": {22: "SSH-2.0-Cisco-1.25"},
            "mac_info": {"mac": "00:1B:67:AA:BB:CC", "vendor": "Cisco Systems"}
        },
        {
            "name": "Windows Server",
            "host_ip": "192.168.1.50",
            "open_ports": [135, 139, 445, 3389],
            "hostname": "WIN-SERVER-01",
            "service_info": {},
            "mac_info": {"mac": "00:26:55:11:22:33", "vendor": "Dell Inc."}
        },
        {
            "name": "Linux Web Server",
            "host_ip": "192.168.1.80",
            "open_ports": [22, 80, 443],
            "hostname": "web-server-01",
            "service_info": {
                22: "OpenSSH_7.4 (Ubuntu)",
                80: "HTTP/1.1 200 OK\nServer: Apache/2.4.41 (Ubuntu)"
            },
            "mac_info": {"mac": "00:E0:4C:44:55:66", "vendor": "Realtek"}
        },
        {
            "name": "Network Printer",
            "host_ip": "192.168.1.200",
            "open_ports": [80, 631, 9100],
            "hostname": "hp-printer-01",
            "service_info": {},
            "mac_info": {"mac": "00:11:85:77:88:99", "vendor": "Canon"}
        },
        {
            "name": "VMware Virtual Machine",
            "host_ip": "192.168.1.120",
            "open_ports": [22, 80],
            "hostname": "vm-ubuntu-01",
            "service_info": {22: "OpenSSH_8.9p1 Ubuntu-3ubuntu0.1"},
            "mac_info": {"mac": "00:0C:29:AA:BB:CC", "vendor": "VMware"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        print(f"   IP: {test_case['host_ip']}")
        print(f"   Hostname: {test_case['hostname']}")
        print(f"   Open Ports: {test_case['open_ports']}")
        print(f"   MAC Vendor: {test_case['mac_info'].get('vendor', 'Unknown')}")
        
        # Test device identification
        try:
            device_type = service._identify_device_type(
                host_ip=test_case['host_ip'],
                open_ports=test_case['open_ports'],
                hostname=test_case['hostname'],
                service_info=test_case['service_info'],
                mac_info=test_case['mac_info']
            )
            print(f"   🎯 Identified as: {device_type}")
            
            # Test individual components
            banner_clues = service._analyze_service_banners(test_case['service_info'])
            vendor_clues = service._analyze_vendor_info(test_case['mac_info'])
            
            if banner_clues.get('os_hints'):
                print(f"   📡 Banner OS hints: {banner_clues['os_hints']}")
            if banner_clues.get('software_hints'):
                print(f"   💻 Software detected: {banner_clues['software_hints']}")
            if vendor_clues.get('device_hints'):
                print(f"   🏭 Vendor hints: {vendor_clues['device_hints']}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Device Identification Test Complete!")

if __name__ == "__main__":
    test_device_identification()