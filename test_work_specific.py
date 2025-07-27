#!/usr/bin/env python3
"""
Test script for the new admin_work_specific endpoint
Tests both WebSocket and HTTP REST API implementations
"""

import asyncio
import json
import websockets
import requests
from requests.auth import HTTPBasicAuth
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WS_URL = "ws://localhost:8000/api/ws"
HTTP_BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Letmein!')

class TestWorkSpecific:
    def __init__(self):
        self.session_token = None
        
    async def test_websocket_flow(self):
        """Test the WebSocket implementation of admin_work_specific"""
        logger.info("🌐 Testing WebSocket admin_work_specific implementation...")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Step 1: Authenticate
                logger.info("🔐 Authenticating with WebSocket...")
                auth_msg = {
                    "type": "auth_request",
                    "request_id": "auth_001",
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                }
                await websocket.send(json.dumps(auth_msg))
                
                # Wait for auth response (may receive welcome message first)
                max_attempts = 3
                auth_response = None
                
                for attempt in range(max_attempts):
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    logger.info(f"📥 Message {attempt + 1}: {response_data}")
                    
                    # Check if this is the auth response we're looking for
                    if (response_data.get('type') == 'auth_response' or 
                        (response_data.get('type') in ['success', 'error'] and 
                         response_data.get('request_id') == 'auth_001')):
                        auth_response = response_data
                        break
                    elif response_data.get('type') == 'welcome':
                        # Welcome message is expected, continue waiting for auth response
                        logger.info("📥 Received welcome message, waiting for auth response...")
                        continue
                
                if not auth_response:
                    logger.error("❌ No authentication response received")
                    return False
                    
                if not auth_response.get('authenticated'):
                    logger.error("❌ Authentication failed")
                    return False
                    
                self.session_token = auth_response.get('session_token')
                logger.info(f"✅ Authenticated! Session token: {self.session_token[:10]}...")
                
                # Step 2: Add a test callsign to queue (public operation)
                test_callsign = "W1TEST"
                logger.info(f"📝 Adding {test_callsign} to queue...")
                register_msg = {
                    "type": "register_callsign",
                    "request_id": "register_001",
                    "callsign": test_callsign
                }
                await websocket.send(json.dumps(register_msg))
                
                # Wait for registration response
                response = await websocket.recv()
                register_response = json.loads(response)
                logger.info(f"📥 Register response: {register_response}")
                
                if register_response.get('type') != 'success':
                    logger.error("❌ Failed to register test callsign")
                    return False
                
                # Step 3: Test admin_work_specific
                logger.info(f"🎯 Testing admin_work_specific for {test_callsign}...")
                work_specific_msg = {
                    "type": "admin_work_specific",
                    "request_id": "work_specific_001",
                    "session_token": self.session_token,
                    "callsign": test_callsign
                }
                await websocket.send(json.dumps(work_specific_msg))
                
                # Wait for work specific response
                response = await websocket.recv()
                work_response = json.loads(response)
                logger.info(f"📥 Work specific response: {work_response}")
                
                if work_response.get('type') == 'success':
                    logger.info("✅ WebSocket admin_work_specific test PASSED!")
                    return True
                else:
                    logger.error(f"❌ WebSocket admin_work_specific test FAILED: {work_response}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ WebSocket test error: {e}")
            return False
    
    def test_http_flow(self):
        """Test the HTTP REST API implementation of admin_work_specific"""
        logger.info("🌐 Testing HTTP REST admin_work_specific implementation...")
        
        try:
            # Step 1: Add a test callsign to queue
            test_callsign = "W2TEST"
            logger.info(f"📝 Adding {test_callsign} to queue via HTTP...")
            
            register_response = requests.post(
                f"{HTTP_BASE_URL}/api/queue/register",
                json={"callsign": test_callsign}
            )
            
            if register_response.status_code != 200:
                logger.error(f"❌ Failed to register {test_callsign}: {register_response.text}")
                return False
                
            logger.info(f"✅ Successfully registered {test_callsign}")
            
            # Step 2: Test admin work specific endpoint
            logger.info(f"🎯 Testing HTTP admin work specific for {test_callsign}...")
            
            work_response = requests.post(
                f"{HTTP_BASE_URL}/api/admin/queue/work/{test_callsign}",
                auth=HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            
            if work_response.status_code == 200:
                response_data = work_response.json()
                logger.info(f"📥 Work specific response: {response_data}")
                logger.info("✅ HTTP admin_work_specific test PASSED!")
                return True
            else:
                logger.error(f"❌ HTTP admin_work_specific test FAILED: {work_response.status_code} - {work_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ HTTP test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run both WebSocket and HTTP tests"""
        logger.info("🚀 Starting admin_work_specific endpoint tests...")
        logger.info("=" * 60)
        
        # Test WebSocket implementation
        ws_success = await self.test_websocket_flow()
        logger.info("=" * 60)
        
        # Test HTTP implementation
        http_success = self.test_http_flow()
        logger.info("=" * 60)
        
        # Summary
        logger.info("📊 TEST SUMMARY:")
        logger.info(f"   WebSocket admin_work_specific: {'✅ PASSED' if ws_success else '❌ FAILED'}")
        logger.info(f"   HTTP admin_work_specific: {'✅ PASSED' if http_success else '❌ FAILED'}")
        
        if ws_success and http_success:
            logger.info("🎉 ALL TESTS PASSED! Both implementations working correctly.")
            return True
        else:
            logger.error("💥 Some tests failed. Check the backend implementation.")
            return False

async def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("🔧 ADMIN_WORK_SPECIFIC ENDPOINT TEST SUITE")
    print("   Testing both WebSocket and HTTP REST implementations")
    print("   Make sure the backend server is running on localhost:8000")
    print("="*80 + "\n")
    
    tester = TestWorkSpecific()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎊 All tests completed successfully!")
        exit(0)
    else:
        print("\n💔 Some tests failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
