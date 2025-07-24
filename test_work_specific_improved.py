#!/usr/bin/env python3
"""
Test script for improved admin_work_specific endpoint
Tests both WebSocket and HTTP implementations with the new "already current QSO" logic
"""

import asyncio
import json
import time
import requests
import websockets
from base64 import b64encode

# Configuration
WS_URL = "ws://localhost:8000/api/ws"
HTTP_BASE = "http://localhost:8000/api"
ADMIN_USER = "admin"
ADMIN_PASS = "Letmein!"

class TestWorkSpecificImproved:
    def __init__(self):
        self.session_token = None
        self.test_results = {
            'websocket_auth': False,
            'websocket_work_from_queue': False,
            'websocket_work_already_current': False,
            'http_work_from_queue': False,
            'http_work_already_current': False,
            'system_activated': False
        }

    def get_auth_headers(self):
        credentials = b64encode(f"{ADMIN_USER}:{ADMIN_PASS}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    async def send_and_wait_for_response(self, websocket, message, timeout=5.0):
        """Send a message and wait for the specific response (handling broadcasts)"""
        request_id = message["request_id"]
        await websocket.send(json.dumps(message))
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                
                # If this message has the matching request_id, it's our response
                if data.get("request_id") == request_id:
                    return data
                # Otherwise it's probably a broadcast, continue waiting
                    
            except asyncio.TimeoutError:
                continue
                
        raise TimeoutError(f"No response received for request {request_id}")

    async def test_websocket_functionality(self):
        """Test WebSocket admin_work_specific with improved logic"""
        print("\n🔗 Testing WebSocket admin_work_specific functionality...")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Handle welcome message
                welcome = await websocket.recv()
                welcome_data = json.loads(welcome)
                if welcome_data.get('type') == 'welcome':
                    print(f"✅ Received welcome: {welcome_data.get('data', {}).get('server_version', 'Unknown')}")
                
                # Authenticate
                auth_msg = {
                    "type": "auth_request",
                    "request_id": "auth_test_001",
                    "username": ADMIN_USER,
                    "password": ADMIN_PASS
                }
                await websocket.send(json.dumps(auth_msg))
                
                auth_response = await websocket.recv()
                auth_data = json.loads(auth_response)
                
                if auth_data.get('type') == 'auth_response':
                    if auth_data.get('authenticated'):
                        self.session_token = auth_data.get('session_token')
                        self.test_results['websocket_auth'] = True
                        print("✅ WebSocket authentication successful")
                        print(f"   Session token expires: {auth_data.get('expires_at')}")
                    else:
                        print(f"❌ WebSocket authentication failed: {auth_data.get('message')}")
                        return
                else:
                    print(f"❌ Unexpected auth response type: {auth_data.get('type')}")
                    print(f"   Full response: {auth_data}")
                    return
                
                # Check current system status first, then ensure it's active
                status_check_msg = {
                    "type": "get_queue_status",
                    "request_id": "status_check_001"
                }
                await websocket.send(json.dumps(status_check_msg))
                status_response = await websocket.recv()
                status_data = json.loads(status_response)
                
                current_system_active = status_data.get('data', {}).get('system_active', False)
                print(f"ℹ️ Current system status: {'ACTIVE' if current_system_active else 'INACTIVE'}")
                
                if not current_system_active:
                    # System is inactive, activate it
                    toggle_msg = {
                        "type": "admin_toggle_system",
                        "request_id": "toggle_test_001",
                        "session_token": self.session_token
                    }
                    await websocket.send(json.dumps(toggle_msg))
                    toggle_response = await websocket.recv()
                    toggle_data = json.loads(toggle_response)
                    
                    if toggle_data.get('type') == 'success':
                        system_active = toggle_data.get('data', {}).get('system_active', False)
                        self.test_results['system_activated'] = system_active
                        print(f"✅ System activated: {'ACTIVE' if system_active else 'INACTIVE'}")
                    else:
                        print(f"⚠️ Failed to toggle system: {toggle_data.get('message')}")
                else:
                    # System is already active
                    self.test_results['system_activated'] = True
                    print("✅ System already active")
                
                # Register a test callsign to work with
                register_msg = {
                    "type": "register_callsign",
                    "request_id": "reg_test_001",
                    "callsign": "W1ABC"
                }
                register_data = await self.send_and_wait_for_response(websocket, register_msg)
                
                if register_data.get('type') == 'success':
                    print("✅ Registered W1ABC in queue")
                else:
                    print(f"⚠️ Could not register W1ABC: {register_data.get('message')}")
                
                # Test 1: Work callsign from queue
                work_msg = {
                    "type": "admin_work_specific",
                    "request_id": "work_queue_001",
                    "session_token": self.session_token,
                    "callsign": "W1ABC"
                }
                work_data = await self.send_and_wait_for_response(websocket, work_msg)
                
                if work_data.get('type') == 'success':
                    self.test_results['websocket_work_from_queue'] = True
                    print("✅ WebSocket: Successfully worked W1ABC from queue")
                    print(f"   Message: {work_data.get('message')}")
                else:
                    print(f"❌ WebSocket: Failed to work W1ABC from queue")
                    print(f"   Error: {work_data.get('error_code', 'UNKNOWN')} - {work_data.get('message', 'No message')}")
                
                # Test 2: Try to work the same callsign again (now it's current QSO)
                work_again_msg = {
                    "type": "admin_work_specific",
                    "request_id": "work_current_001",
                    "session_token": self.session_token,
                    "callsign": "W1ABC"
                }
                work_again_data = await self.send_and_wait_for_response(websocket, work_again_msg)
                
                if work_again_data.get('type') == 'success':
                    self.test_results['websocket_work_already_current'] = True
                    print("✅ WebSocket: Successfully handled already-current callsign W1ABC")
                    print(f"   Message: {work_again_data.get('message')}")
                else:
                    print(f"❌ WebSocket: Failed to handle already-current callsign")
                    print(f"   Error: {work_again_data.get('error_code', 'UNKNOWN')} - {work_again_data.get('message', 'No message')}")
                
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")

    def test_http_functionality(self):
        """Test HTTP admin_work_specific with improved logic"""
        print("\n🌐 Testing HTTP admin_work_specific functionality...")
        
        try:
            headers = self.get_auth_headers()
            
            # Register another test callsign
            register_response = requests.post(
                f"{HTTP_BASE}/queue/register",
                json={"callsign": "W2XYZ"},
                timeout=10
            )
            
            if register_response.status_code == 200:
                print("✅ Registered W2XYZ in queue via HTTP")
            else:
                print(f"⚠️ Could not register W2XYZ via HTTP: {register_response.text}")
            
            # Test 1: Work callsign from queue
            work_response = requests.post(
                f"{HTTP_BASE}/admin/queue/work/W2XYZ",
                headers=headers,
                timeout=10
            )
            
            if work_response.status_code == 200:
                work_data = work_response.json()
                self.test_results['http_work_from_queue'] = True
                print("✅ HTTP: Successfully worked W2XYZ from queue")
                print(f"   Message: {work_data.get('message')}")
                print(f"   Was already current: {work_data.get('was_already_current', False)}")
            else:
                print(f"❌ HTTP: Failed to work W2XYZ from queue: {work_response.text}")
            
            # Test 2: Try to work the same callsign again (now it's current QSO)
            work_again_response = requests.post(
                f"{HTTP_BASE}/admin/queue/work/W2XYZ",
                headers=headers,
                timeout=10
            )
            
            if work_again_response.status_code == 200:
                work_again_data = work_again_response.json()
                self.test_results['http_work_already_current'] = True
                print("✅ HTTP: Successfully handled already-current callsign W2XYZ")
                print(f"   Message: {work_again_data.get('message')}")
                print(f"   Was already current: {work_again_data.get('was_already_current', False)}")
            else:
                print(f"❌ HTTP: Failed to handle already-current callsign: {work_again_response.text}")
                
        except Exception as e:
            print(f"❌ HTTP test error: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\nResults: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! The improved admin_work_specific logic is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")

async def main():
    """Main test execution"""
    print("🚀 Starting improved admin_work_specific endpoint tests...")
    print("Testing the new logic that handles 'already current QSO' gracefully")
    
    tester = TestWorkSpecificImproved()
    
    # Run WebSocket tests
    await tester.test_websocket_functionality()
    
    # Small delay between tests
    await asyncio.sleep(1)
    
    # Run HTTP tests
    tester.test_http_functionality()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
