#!/usr/bin/env python3
"""
Test script to verify QSO completion SSE events
"""

import requests
import asyncio
import aiohttp
import json
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

async def listen_for_sse_events():
    """Listen for SSE events including QSO completion"""
    print("🎧 Starting SSE listener for QSO completion events...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/events") as response:
                if response.status == 200:
                    print("✅ Connected to SSE stream")
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith('data: '):
                            try:
                                data_json = line_str[6:]  # Remove 'data: ' prefix
                                event_data = json.loads(data_json)
                                event_type = event_data.get('type')
                                
                                if event_type == 'qso_completed':
                                    print(f"🎉 QSO COMPLETION EVENT RECEIVED!")
                                    data = event_data.get('data', {})
                                    callsign = data.get('callsign', 'Unknown')
                                    message = data.get('message', 'No message')
                                    source = data.get('source', 'unknown')
                                    print(f"   Callsign: {callsign}")
                                    print(f"   Message: {message}")
                                    print(f"   Source: {source}")
                                    print(f"   Full Event: {event_data}")
                                    return True  # Event received successfully
                                else:
                                    print(f"📡 Other event: {event_type}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"⚠️  JSON decode error: {e}")
                                
                else:
                    print(f"❌ Failed to connect to SSE: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ SSE listener error: {e}")
        return False

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
                print(f"   Completed QSO with: {cleared_qso.get('callsign', 'Unknown')}")
            return True
        else:
            print(f"❌ QSO completion failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ QSO completion error: {e}")
        return False

async def test_qso_completion_event():
    """Test QSO completion SSE event"""
    print("🧪 Testing QSO Completion SSE Event")
    print("=" * 50)
    
    # Start SSE listener in background
    sse_task = asyncio.create_task(listen_for_sse_events())
    
    # Give SSE time to connect
    await asyncio.sleep(2)
    
    # Trigger QSO completion
    success = complete_current_qso()
    
    if not success:
        print("⚠️  Could not complete QSO - test incomplete")
        sse_task.cancel()
        return False
    
    # Wait for SSE event (timeout after 10 seconds)
    try:
        event_received = await asyncio.wait_for(sse_task, timeout=10.0)
        return event_received
    except asyncio.TimeoutError:
        print("⏰ Timeout waiting for QSO completion event")
        sse_task.cancel()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_qso_completion_event())
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 QSO completion SSE event test PASSED!")
    else:
        print("❌ QSO completion SSE event test FAILED!")
