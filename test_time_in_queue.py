#!/usr/bin/env python3
"""
Test script to verify time_in_queue functionality
"""

import requests
import json
import time
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

def test_time_in_queue():
    """Test that queue entries include time_in_queue"""
    print("🧪 Testing time_in_queue functionality...")
    
    try:
        # Get admin queue
        response = requests.get(
            f"{BASE_URL}/api/admin/queue",
            auth=HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP Admin Queue successful!")
            print(f"   Total entries: {data.get('total', 0)}")
            
            queue = data.get('queue', [])
            for i, entry in enumerate(queue):
                callsign = entry.get('callsign', 'Unknown')
                time_in_queue = entry.get('time_in_queue', 'Missing!')
                timestamp = entry.get('timestamp', 'No timestamp')
                print(f"   {i+1}. {callsign}: {time_in_queue}s in queue (since {timestamp})")
            
            if queue and all('time_in_queue' in entry for entry in queue):
                print("✅ All queue entries have time_in_queue field!")
                return True
            elif not queue:
                print("ℹ️  Queue is empty - cannot test time_in_queue")
                return True
            else:
                print("❌ Some queue entries missing time_in_queue field")
                return False
        else:
            print(f"❌ HTTP Admin Queue failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP Admin Queue error: {e}")
        return False

def test_public_queue_time():
    """Test that public queue also includes time_in_queue"""
    print("\n🧪 Testing public queue time_in_queue...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/queue/list", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Public Queue successful!")
            print(f"   Total entries: {data.get('total', 0)}")
            
            queue = data.get('queue', [])
            for i, entry in enumerate(queue):
                callsign = entry.get('callsign', 'Unknown')
                time_in_queue = entry.get('time_in_queue', 'Missing!')
                print(f"   {i+1}. {callsign}: {time_in_queue}s in queue")
            
            if queue and all('time_in_queue' in entry for entry in queue):
                print("✅ All public queue entries have time_in_queue field!")
                return True
            elif not queue:
                print("ℹ️  Public queue is empty - cannot test time_in_queue")
                return True
            else:
                print("❌ Some public queue entries missing time_in_queue field")
                return False
        else:
            print(f"❌ Public Queue failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Public Queue error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing time_in_queue Implementation")
    print("=" * 50)
    
    admin_success = test_time_in_queue()
    public_success = test_public_queue_time()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Admin Queue time_in_queue: {'✅ PASS' if admin_success else '❌ FAIL'}")
    print(f"   Public Queue time_in_queue: {'✅ PASS' if public_success else '❌ FAIL'}")
    
    if all([admin_success, public_success]):
        print("\n🎉 time_in_queue functionality working correctly!")
    else:
        print("\n⚠️  Some time_in_queue functionality failed")
