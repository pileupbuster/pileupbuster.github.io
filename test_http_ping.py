#!/usr/bin/env python3
"""
Simple HTTP ping test script
"""

import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

def test_http_ping():
    """Test the HTTP admin ping endpoint"""
    print("🏓 Testing HTTP Admin Ping Endpoint...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/ping",
            auth=HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP Ping successful!")
            print(f"   Message: {data.get('message')}")
            print(f"   Username: {data.get('username')}")
            print(f"   Server Time: {data.get('server_time')}")
            print(f"   Ping Type: {data.get('ping_type')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Full Response: {data}")
            return True
        else:
            print(f"❌ HTTP Ping failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP Ping error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing HTTP Ping Endpoint")
    print("=" * 40)
    
    success = test_http_ping()
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   HTTP Admin Ping: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 HTTP ping endpoint working correctly!")
    else:
        print("\n⚠️  HTTP ping endpoint failed")
