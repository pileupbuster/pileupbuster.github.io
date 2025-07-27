#!/usr/bin/env python3
"""
Complete test to verify SSE QSO completion events
"""

import requests
from requests.auth import HTTPBasicAuth
import asyncio
import websockets
import json
import threading
import time

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

def listen_for_sse_events():
    """Listen for SSE events in background"""
    print("🎧 Starting SSE listener in background...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/events/stream",
            headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ SSE connection failed: {response.status_code}")
            return
            
        print("✅ SSE connected, listening for events...")
        
        event_type = None
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith("event:"):
                    event_type = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    event_data = line.replace("data:", "").strip()
                    if event_type == "qso_completed":
                        print(f"🎉 QSO COMPLETION SSE EVENT RECEIVED!")
                        try:
                            data_json = json.loads(event_data)
                            print(f"📦 Event Data: {json.dumps(data_json, indent=2)}")
                        except:
                            print(f"📦 Raw Event Data: {event_data}")
                        return True
                        
    except Exception as e:
        print(f"❌ SSE error: {e}")
        return False

async def start_qso_websocket():
    """Start a QSO via WebSocket"""
    try:
        uri = f"{WS_URL}/api/ws"
        async with websockets.connect(uri) as websocket:
            # Get welcome
            welcome = await websocket.recv()
            
            # Authenticate
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
                print(f"❌ WebSocket auth failed: {auth_data}")
                return False
                
            session_token = auth_data.get("session_token")
            print(f"✅ WebSocket authenticated")
            
            # Start QSO
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
                print(f"✅ QSO started with W1AW")
                return True
            else:
                print(f"❌ QSO start failed: {start_data}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

def complete_qso_http():
    """Complete QSO via HTTP"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/qso/complete",
            auth=HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ QSO completed via HTTP")
            callsign = data.get('cleared_qso', {}).get('callsign', 'Unknown')
            print(f"   Completed QSO with: {callsign}")
            return True
        else:
            print(f"❌ QSO completion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP completion error: {e}")
        return False

def main():
    print("🧪 COMPREHENSIVE SSE QSO COMPLETION TEST")
    print("=" * 60)
    
    # Start SSE listener in background thread
    sse_result = [False]  # Use list for mutable reference
    
    def sse_thread():
        sse_result[0] = listen_for_sse_events()
    
    sse_listener = threading.Thread(target=sse_thread, daemon=True)
    sse_listener.start()
    
    # Give SSE time to connect
    time.sleep(2)
    
    # Start QSO
    print("\n🎬 Starting QSO via WebSocket...")
    qso_started = asyncio.run(start_qso_websocket())
    
    if not qso_started:
        print("❌ Cannot start QSO - test failed")
        return
    
    # Give a moment for QSO to be established
    time.sleep(1)
    
    # Complete QSO
    print("\n🏁 Completing QSO via HTTP...")
    qso_completed = complete_qso_http()
    
    if not qso_completed:
        print("❌ Cannot complete QSO - test failed")
        return
    
    # Wait for SSE event
    print("\n⏳ Waiting for SSE event (up to 10 seconds)...")
    sse_listener.join(timeout=10)
    
    print("\n" + "=" * 60)
    if sse_result[0]:
        print("✅ SUCCESS! SSE QSO completion event was received!")
        print("🎪 The frontend popup notification system is working!")
    else:
        print("❌ FAILED! No SSE QSO completion event was received")
        print("🔍 This indicates the SSE event system may not be working properly")

if __name__ == "__main__":
    main()
