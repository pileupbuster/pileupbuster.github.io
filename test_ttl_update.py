#!/usr/bin/env python3
"""
Test script for the new TTL update API endpoint
"""
import requests
import base64
import os

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def test_rest_api():
    """Test the REST API endpoint"""
    print("Testing REST API endpoint...")
    
    # Create Basic Auth header
    credentials = f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test the new TTL update endpoint
        response = requests.post(f"{BASE_URL}/api/admin/worked-callers/update-ttl", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Updated TTL for {result.get('modified_count', 0)} worked callers")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_websocket_api():
    """Test the WebSocket API endpoint"""
    print("\nTesting WebSocket API...")
    print("Note: WebSocket testing requires a more complex setup.")
    print("You can test the WebSocket endpoint using a WebSocket client with this message:")
    print("""
{
    "type": "auth_request",
    "request_id": "test-auth-1",
    "username": "admin",
    "password": "admin123"
}
    """)
    print("Then send:")
    print("""
{
    "type": "admin_update_worked_callers_ttl",
    "request_id": "test-ttl-1",
    "session_token": "<token_from_auth_response>"
}
    """)

if __name__ == "__main__":
    print("Pileup Buster - TTL Update API Test")
    print("=" * 40)
    
    test_rest_api()
    test_websocket_api()
    
    print("\n" + "=" * 40)
    print("Test completed!")
