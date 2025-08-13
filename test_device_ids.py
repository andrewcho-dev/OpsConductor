#!/usr/bin/env python3
"""
Test device ID generation in discovery.
"""
import asyncio
import sys
import time
import requests
import json

async def test_device_ids():
    """Test device ID generation."""
    print("🔍 Testing Device ID Generation...")
    
    # Discovery configuration
    discovery_config = {
        "network_ranges": ["192.168.50.0/28"],  # Small range for testing
        "common_ports": [22, 80, 443],
        "timeout": 1.0,
        "max_concurrent": 10,
        "enable_snmp": False,
        "enable_service_detection": True,
        "enable_hostname_resolution": True
    }
    
    print(f"🎯 Testing range: {discovery_config['network_ranges'][0]}")
    
    start_time = time.time()
    
    try:
        # Start discovery task
        print("📤 Starting discovery task...")
        start_response = requests.post(
            'https://localhost/api/discovery/discover-memory',
            json=discovery_config,
            timeout=30,
            verify=False
        )
        
        if start_response.status_code != 200:
            raise Exception(f"Failed to start task: {start_response.status_code} - {start_response.text}")
        
        task_data = start_response.json()
        task_id = task_data['task_id']
        print(f"✅ Task started with ID: {task_id}")
        
        # Poll for results
        print("🔄 Polling for results...")
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            try:
                result_response = requests.get(
                    f'https://localhost/api/discovery/discover-memory/{task_id}',
                    timeout=10,
                    verify=False
                )
                
                if result_response.status_code != 200:
                    print(f"❌ Error getting result: {result_response.status_code}")
                    break
                
                result = result_response.json()
                status = result.get('status', 'unknown')
                
                if status == 'completed':
                    devices = result.get('devices', [])
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print(f"\n🎯 DEVICE ID ANALYSIS:")
                    print(f"⏱️  Total time: {duration:.1f} seconds")
                    print(f"📊 Found {len(devices)} devices")
                    
                    if len(devices) > 0:
                        print(f"\n📱 Device ID Details:")
                        device_ids = []
                        for i, device in enumerate(devices):
                            device_id = device.get('id')
                            ip = device.get('ip_address', 'Unknown')
                            hostname = device.get('hostname', 'No hostname')
                            
                            print(f"   Device {i+1}: ID={device_id} (type: {type(device_id)}) IP={ip} Hostname={hostname}")
                            device_ids.append(device_id)
                        
                        # Check for duplicates
                        unique_ids = set(device_ids)
                        print(f"\n🔍 ID Analysis:")
                        print(f"   Total devices: {len(devices)}")
                        print(f"   Unique IDs: {len(unique_ids)}")
                        print(f"   All IDs: {device_ids}")
                        
                        if len(unique_ids) != len(devices):
                            print(f"❌ DUPLICATE IDs FOUND! This is the bug!")
                            duplicates = [id for id in device_ids if device_ids.count(id) > 1]
                            print(f"   Duplicate IDs: {set(duplicates)}")
                        else:
                            print(f"✅ All IDs are unique")
                    else:
                        print("ℹ️  No devices found")
                    
                    return
                    
                elif status == 'failed':
                    error = result.get('error', 'Unknown error')
                    print(f"❌ Discovery failed: {error}")
                    return
                
                # Wait before next poll
                await asyncio.sleep(1)
                attempts += 1
                
            except Exception as e:
                print(f"❌ Error polling: {e}")
                break
        
        print("⏰ Discovery timed out")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_device_ids())