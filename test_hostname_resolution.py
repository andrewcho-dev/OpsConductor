#!/usr/bin/env python3
"""
Test hostname resolution functionality.
"""
import asyncio
import sys
import time
import requests
import json

async def test_hostname_resolution():
    """Test hostname resolution in discovery."""
    print("🌐 Testing Hostname Resolution...")
    
    # Discovery configuration with hostname resolution enabled
    discovery_config = {
        "network_ranges": ["192.168.50.1/32"],  # Test single IP
        "common_ports": [80, 443],
        "timeout": 2.0,
        "max_concurrent": 10,
        "enable_snmp": True,
        "enable_service_detection": True,
        "enable_hostname_resolution": True
    }
    
    print(f"🎯 Testing IP: {discovery_config['network_ranges'][0]}")
    
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
        max_attempts = 60  # 1 minute
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
                progress = result.get('progress', 0)
                message = result.get('message', 'No message')
                
                print(f"📊 Status: {status} - Progress: {progress}% - {message}")
                
                if status == 'completed':
                    devices = result.get('devices', [])
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print(f"\n🎯 HOSTNAME RESOLUTION RESULTS:")
                    print(f"⏱️  Total time: {duration:.1f} seconds")
                    print(f"📊 Found {len(devices)} devices")
                    
                    if len(devices) > 0:
                        for device in devices:
                            ip = device.get('ip_address', 'Unknown')
                            hostname = device.get('hostname', 'No hostname')
                            device_type = device.get('device_type', 'Unknown')
                            ports = device.get('open_ports', [])
                            
                            print(f"\n📱 Device: {ip}")
                            print(f"   🏷️  Hostname: {hostname}")
                            print(f"   🖥️  Type: {device_type}")
                            print(f"   🔌 Ports: {ports}")
                            
                            if hostname and hostname != 'No hostname':
                                print(f"✅ Hostname resolution WORKING!")
                            else:
                                print(f"⚠️  No hostname resolved (may be normal)")
                    else:
                        print("ℹ️  No devices found (may be excluded as existing targets)")
                    
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
    asyncio.run(test_hostname_resolution())