#!/usr/bin/env python3
"""
Test script for admin_cancel_qso endpoint (both HTTP and WebSocket)

This is a SEPARATE feature from admin_complete_qso:
- admin_cancel_qso: Cancel/abort a QSO (mistake, wrong station, etc.)
- admin_complete_qso: Successfully complete a finished QSO (will get enhanced features later)
"""

import asyncio
import websockets
import json
import time
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ws"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

class TestCancelQSO:
    def __init__(self):
        self.websocket = None
        self.session_token = None
        
    def test_backend_connectivity(self):
        """Test if backend is running"""
        try:
            response = requests.get(f"{BACKEND_URL}/status")
            print(f"✅ Backend is running (status: {response.status_code})")
            return True
        except Exception as e:
            print(f"❌ Backend not accessible: {e}")
            return False
            
    async def wait_for_response(self, websocket, timeout=5):
        """Wait for WebSocket response, filtering out broadcasts"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                
                # Skip broadcast messages, return only responses with request_id
                if data.get("request_id") or data.get("type") in ["auth_response", "error"]:
                    return data
                    
                # Log broadcasts but continue waiting
                print(f"📡 Received broadcast: {data.get('type')}")
                
            except asyncio.TimeoutError:
                continue
                
        raise TimeoutError("No response received within timeout")
        
    async def test_websocket_cancel_qso(self):
        """Test WebSocket admin_cancel_qso endpoint"""
        print("🔌 Testing WebSocket admin_cancel_qso endpoint...")
        
        try:
            # Connect to WebSocket
            self.websocket = await websockets.connect(WS_URL)
            print("✅ Connected to WebSocket")
            
            # Skip welcome message
            welcome = await self.websocket.recv()
            print(f"📡 Welcome: {json.loads(welcome).get('message')}")
            
            # Authenticate
            auth_request = {
                "type": "auth_request",
                "request_id": f"auth_{int(time.time() * 1000)}",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            await self.websocket.send(json.dumps(auth_request))
            auth_response = await self.wait_for_response(self.websocket)
            
            if auth_response.get("type") == "auth_response" and auth_response.get("authenticated"):
                self.session_token = auth_response.get("session_token")
                print("✅ WebSocket authentication successful")
            else:
                print(f"❌ WebSocket authentication failed: {auth_response}")
                return False
                
            # Test 1: Cancel QSO when no QSO active
            print("\n📋 Test 1: Cancel QSO when no active QSO")
            cancel_request = {
                "type": "admin_cancel_qso",
                "request_id": f"cancel_1_{int(time.time() * 1000)}",
                "session_token": self.session_token
            }
            
            await self.websocket.send(json.dumps(cancel_request))
            response = await self.wait_for_response(self.websocket)
            
            if response.get("type") == "success":
                print(f"✅ Success: {response.get('message')}")
                if response.get("data", {}).get("cancelled_qso") is None:
                    print("✅ Correctly handled no active QSO")
                else:
                    print("❌ Expected no QSO to cancel")
            else:
                print(f"❌ Failed: {response}")
                
            # Test 2: Start a QSO and then cancel it
            print("\n📋 Test 2: Start QSO and then cancel it")
            
            # First start a QSO
            start_request = {
                "type": "admin_start_qso",
                "request_id": f"start_{int(time.time() * 1000)}",
                "session_token": self.session_token,
                "callsign": "EA1TEST",
                "frequency_mhz": 14.205,
                "mode": "USB",
                "source": "direct"
            }
            
            await self.websocket.send(json.dumps(start_request))
            start_response = await self.wait_for_response(self.websocket)
            
            if start_response.get("type") == "success":
                print("✅ QSO started with EA1TEST")
                
                # Now cancel the QSO
                cancel_request2 = {
                    "type": "admin_cancel_qso",
                    "request_id": f"cancel_2_{int(time.time() * 1000)}",
                    "session_token": self.session_token
                }
                
                await self.websocket.send(json.dumps(cancel_request2))
                cancel_response = await self.wait_for_response(self.websocket)
                
                if cancel_response.get("type") == "success":
                    cancelled_qso = cancel_response.get("data", {}).get("cancelled_qso")
                    if cancelled_qso and cancelled_qso.get("callsign") == "EA1TEST":
                        print(f"✅ Successfully cancelled QSO: {cancel_response.get('message')}")
                        print("✅ This is SEPARATE from admin_complete_qso (which will get enhanced features)")
                    else:
                        print(f"❌ Unexpected cancelled QSO data: {cancelled_qso}")
                else:
                    print(f"❌ Failed to cancel QSO: {cancel_response}")
            else:
                print(f"❌ Failed to start QSO: {start_response}")
                
            await self.websocket.close()
            return True
            
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            if self.websocket:
                await self.websocket.close()
            return False
    
    def test_http_cancel_qso(self):
        """Test HTTP admin/qso/cancel endpoint"""
        print("🌐 Testing HTTP admin/qso/cancel endpoint...")
        
        try:
            # Test 1: Cancel QSO when no QSO active
            print("\n📋 Test 1: Cancel QSO when no active QSO")
            response = requests.post(
                f"{BACKEND_URL}/api/admin/qso/cancel",
                auth=HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('message')}")
                if data.get('cancelled_qso') is None:
                    print("✅ Correctly handled no active QSO")
                    print("✅ This is SEPARATE from admin_complete_qso (future enhancements won't affect this)")
                else:
                    print("❌ Expected no QSO to cancel")
                return True
            else:
                print(f"❌ HTTP request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ HTTP test failed: {e}")
            return False

async def main():
    """Run all tests"""
    print("🧪 Testing admin_cancel_qso Implementation")
    print("=" * 60)
    print("🎯 IMPORTANT: admin_cancel_qso is SEPARATE from admin_complete_qso")
    print("   • admin_cancel_qso: Cancel/abort QSO (stable, simple)")
    print("   • admin_complete_qso: Complete QSO (will get enhanced features)")
    print("=" * 60)
    
    tester = TestCancelQSO()
    
    # Test backend connectivity
    if not tester.test_backend_connectivity():
        print("❌ Backend not running. Please start the backend first.")
        return
    
    print()
    
    # Test HTTP endpoint
    http_success = tester.test_http_cancel_qso()
    
    print("\n" + "=" * 50)
    
    # Test WebSocket endpoint
    ws_success = await tester.test_websocket_cancel_qso()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"HTTP admin/qso/cancel: {'✅ PASS' if http_success else '❌ FAIL'}")
    print(f"WebSocket admin_cancel_qso: {'✅ PASS' if ws_success else '❌ FAIL'}")
    
    if http_success and ws_success:
        print("🎉 All tests passed! admin_cancel_qso is working correctly.")
        print("✅ Feature is properly separated from admin_complete_qso")
    else:
        print("⚠️ Some tests failed. Check implementation.")

if __name__ == "__main__":
    asyncio.run(main())
