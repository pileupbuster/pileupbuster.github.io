#!/usr/bin/env python3
"""
Simple test script to trigger QSO completion and check for SSE events
"""

import requests
from requests.auth import HTTPBasicAuth
import asyncio
import websockets
import json
import base64

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

async def authenticate_and_start_qso():
    """Authenticate via WebSocket and start a test QSO using the same connection"""
    try:
        uri = f"{WS_URL}/api/ws"
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            print(f"📝 Received welcome: {json.loads(welcome).get('message', 'Connected')}")
            
            # Send authentication request
            auth_request = {
                "type": "auth_request",
                "request_id": "auth_test",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            await websocket.send(json.dumps(auth_request))
            auth_response = await websocket.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get("authenticated") != True:
                print(f"❌ WebSocket authentication failed: {auth_data}")
                return False
                
            session_token = auth_data.get("session_token")
            print(f"✅ WebSocket authentication successful! Token: {session_token[:8]}...")
            
            # Now start QSO with the same connection
            start_request = {
                "type": "admin_start_qso",
                "request_id": "start_test",
                "session_token": session_token,
                "callsign": "W1AW",
                "frequency_mhz": 14.205,
                "mode": "SSB",
                "source": "direct"
            }
            
            await websocket.send(json.dumps(start_request))
            start_response = await websocket.recv()
            start_data = json.loads(start_response)
            
            if start_data.get("type") == "success":
                print(f"✅ Test QSO started with W1AW via WebSocket")
                return True
            else:
                print(f"❌ Failed to start QSO via WebSocket: {start_data}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket operation error: {e}")
        return False

def get_current_qso():
    """Get the current QSO"""
    try:
        response = requests.get(f"{BASE_URL}/api/queue/current", timeout=5)
        if response.status_code == 200:
            data = response.json()
            current_qso = data.get('current_qso')
            if current_qso:
                print(f"📻 Current QSO: {current_qso.get('callsign', 'Unknown')}")
                return current_qso
            else:
                print("ℹ️  No current QSO active")
                return None
        else:
            print(f"❌ Failed to get current QSO: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting current QSO: {e}")
        return None

def complete_current_qso():
    """Complete the current QSO via HTTP"""
    print("🏁 Completing current QSO via HTTP...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/qso/complete",
            auth=HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ QSO completion successful!")
            print(f"   Message: {data.get('message')}")
            cleared_qso = data.get('cleared_qso')
            if cleared_qso:
                callsign = cleared_qso.get('callsign', 'Unknown')
                print(f"   Completed QSO with: {callsign}")
                print(f"   🎉 Expected popup message: '{callsign} Just busted the pileup, with PileupBuster!'")
            return True
        else:
            print(f"❌ QSO completion failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ QSO completion error: {e}")
        return False

def start_qso_for_testing():
    """Start a test QSO via WebSocket if none exists"""
    print("🎬 Starting test QSO via WebSocket...")
    
    # Run the async function
    try:
        return asyncio.run(authenticate_and_start_qso())
    except Exception as e:
        print(f"❌ Error in async QSO start: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing QSO Completion with SSE Event")
    print("=" * 60)
    
    # Check if there's already a QSO in progress
    current_qso = get_current_qso()
    
    # If no QSO, start a test one
    if not current_qso:
        if not start_qso_for_testing():
            print("❌ Cannot start test QSO - exiting")
            exit(1)
    
    # Complete the QSO
    success = complete_current_qso()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ QSO completion test completed!")
        print("📡 An SSE event 'qso_completed' should have been sent to the frontend")
        print("🎪 Frontend should show popup with the 'Just busted the pileup' message")
    else:
        print("❌ QSO completion test failed!")
    
    print("\n💡 To see the SSE events, connect to: " + BASE_URL + "/api/events")
    print("💡 Look for event type 'qso_completed' with the popup message")
