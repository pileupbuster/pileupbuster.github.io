#!/usr/bin/env python3
"""
Test script for the new ping endpoints (HTTP and WebSocket)
"""

import requests
import websocket
import json
import time
import base64
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ws"
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
            return True
        else:
            print(f"❌ HTTP Ping failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP Ping error: {e}")
        return False

def test_websocket_ping():
    """Test the WebSocket admin ping endpoint"""
    print("\n🏓 Testing WebSocket Admin Ping Endpoint...")
    
    try:
        # Connect to WebSocket
        ws = websocket.create_connection(WS_URL, timeout=5)
        print("✅ WebSocket connected")
        
        # Receive welcome message
        welcome = ws.recv()
        print(f"📩 Welcome: {json.loads(welcome)['message']}")
        
        # Authenticate
        auth_request = {
            "type": "auth_request",
            "request_id": "auth_001",
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        ws.send(json.dumps(auth_request))
        auth_response = json.loads(ws.recv())
        
        if not auth_response.get('authenticated'):
            print(f"❌ Authentication failed: {auth_response.get('message')}")
            return False
            
        print("✅ WebSocket authenticated successfully")
        session_token = auth_response['session_token']
        
        # Send admin ping
        ping_request = {
            "type": "admin_ping",
            "request_id": "ping_001",
            "session_token": session_token
        }
        
        print("📤 Sending admin ping...")
        ws.send(json.dumps(ping_request))
        
        # Receive pong response
        pong_response = json.loads(ws.recv())
        
        if pong_response.get('type') == 'success' and pong_response.get('message') == 'pong':
            print(f"✅ WebSocket Ping successful!")
            print(f"   Message: {pong_response.get('message')}")
            print(f"   Request ID: {pong_response.get('request_id')}")
            data = pong_response.get('data', {})
            print(f"   Server Time: {data.get('server_time')}")
            print(f"   Authenticated: {data.get('authenticated')}")
            print(f"   Ping Type: {data.get('ping_type')}")
            
            ws.close()
            return True
        else:
            print(f"❌ WebSocket Ping failed")
            print(f"   Response: {pong_response}")
            ws.close()
            return False
            
    except Exception as e:
        print(f"❌ WebSocket Ping error: {e}")
        return False

def test_public_ping():
    """Test the public (non-authenticated) ping endpoint"""
    print("\n🏓 Testing Public Ping Endpoint...")
    
    try:
        # Connect to WebSocket
        ws = websocket.create_connection(WS_URL, timeout=5)
        print("✅ WebSocket connected")
        
        # Receive welcome message
        welcome = ws.recv()
        print(f"📩 Welcome: {json.loads(welcome)['message']}")
        
        # Send public ping (no authentication)
        ping_request = {
            "type": "ping",
            "request_id": "public_ping_001"
        }
        
        print("📤 Sending public ping...")
        ws.send(json.dumps(ping_request))
        
        # Receive pong response
        pong_response = json.loads(ws.recv())
        
        if pong_response.get('type') == 'pong':
            print(f"✅ Public Ping successful!")
            print(f"   Type: {pong_response.get('type')}")
            print(f"   Timestamp: {pong_response.get('timestamp')}")
            
            ws.close()
            return True
        else:
            print(f"❌ Public Ping failed")
            print(f"   Response: {pong_response}")
            ws.close()
            return False
            
    except Exception as e:
        print(f"❌ Public Ping error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Ping Endpoints")
    print("=" * 50)
    
    # Test all ping endpoints
    http_success = test_http_ping()
    ws_success = test_websocket_ping()
    public_success = test_public_ping()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   HTTP Admin Ping: {'✅ PASS' if http_success else '❌ FAIL'}")
    print(f"   WebSocket Admin Ping: {'✅ PASS' if ws_success else '❌ FAIL'}")
    print(f"   WebSocket Public Ping: {'✅ PASS' if public_success else '❌ FAIL'}")
    
    if all([http_success, ws_success, public_success]):
        print("\n🎉 All ping endpoints working correctly!")
    else:
        print("\n⚠️  Some ping endpoints failed")
