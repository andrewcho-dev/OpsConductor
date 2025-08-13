#!/usr/bin/env python3
"""
Test script for Celery-based discovery performance.
"""
import asyncio
import sys
import time
import requests

async def test_celery_discovery():
    """Test Celery-based Windows discovery."""
    print("🚀 Testing CELERY-BASED Discovery...")
    
    # Discovery configuration optimized for speed
    discovery_config = {
        "network_ranges": ["192.168.50.0/24"],
        "common_ports": [135, 139, 445, 3389, 5985, 5986, 22, 80, 443],
        "timeout": 2.0,
        "max_concurrent": 200,
        "enable_snmp": True,
        "enable_service_detection": True,
        "enable_hostname_resolution": True
    }
    
    print(f"🌐 Network: {discovery_config['network_ranges'][0]}")
    print(f"⚡ Optimized: {discovery_config['timeout']}s timeout, {discovery_config['max_concurrent']} concurrent")
    print(f"🔌 Ports: {discovery_config['common_ports']}")
    
    start_time = time.time()
    
    try:
        # Start discovery task
        print("📤 Starting Celery discovery task...")
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
        max_attempts = 120  # 2 minutes
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
                    
                    print(f"\n🎯 CELERY RESULTS:")
                    print(f"⏱️  Total time: {duration:.1f} seconds")
                    print(f"📊 Found {len(devices)} devices")
                    print(f"🚀 Speed: {254/duration:.1f} IPs/second")
                    
                    windows_count = sum(1 for d in devices if 'windows' in d.get('device_type', '').lower())
                    print(f"🪟 Windows devices: {windows_count}")
                    
                    if duration < 15:
                        print("🎉 EXCELLENT: Celery discovery is FAST!")
                    elif duration < 30:
                        print("✅ GOOD: Much better than synchronous")
                    else:
                        print("⚠️  IMPROVED: Better but could be faster")
                    
                    # Show some Windows devices
                    if windows_count > 0:
                        print(f"\n🪟 Windows Devices Found:")
                        for device in devices:
                            if 'windows' in device.get('device_type', '').lower():
                                ip = device.get('ip_address', 'Unknown')
                                device_type = device.get('device_type', 'Unknown')
                                ports = device.get('open_ports', [])
                                ports_str = ', '.join(map(str, ports[:5]))
                                if len(ports) > 5:
                                    ports_str += f" (+{len(ports)-5} more)"
                                print(f"   • {ip}: {device_type} - ports: {ports_str}")
                    
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
    asyncio.run(test_celery_discovery())