#!/usr/bin/env python3
"""
WebSocket Test Client for Pileup Buster

This is a simple test client to verify the WebSocket server functionality.
Run this script to test basic WebSocket operations.
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime


async def test_websocket_connection():
    """Test basic WebSocket connection and functionality."""
    
    uri = "ws://localhost:8000/ws/connect"
    print(f"Connecting to WebSocket server at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Listen for welcome message
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                print(f"📨 Received welcome: {welcome_data.get('event')} - {welcome_data.get('data', {}).get('message')}")
            except asyncio.TimeoutError:
                print("⏰ No welcome message received")
            
            # Test 1: Send ping
            print("\n🏓 Testing ping...")
            ping_msg = {
                "id": "test-ping-1",
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(ping_msg))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'pong':
                print(f"✅ Ping successful! Server time: {response_data.get('data', {}).get('server_time')}")
                print(f"   Connection count: {response_data.get('data', {}).get('connection_count')}")
            else:
                print(f"❌ Unexpected ping response: {response_data}")
            
            # Test 2: Try an unauthenticated public request
            print("\n📊 Testing public request (should work without auth)...")
            public_request = {
                "id": "test-public-1",
                "type": "request",
                "operation": "public.get_status",
                "data": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(public_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('success'):
                print(f"✅ Public request successful: {response_data.get('data', {}).get('message')}")
            else:
                print(f"❌ Public request failed: {response_data}")
            
            # Test 3: Try an admin request without auth (should fail)
            print("\n🔒 Testing admin request without auth (should fail)...")
            admin_request = {
                "id": "test-admin-1",
                "type": "request",
                "operation": "admin.get_queue",
                "data": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(admin_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'error' and 'Authentication required' in response_data.get('error', ''):
                print("✅ Admin request properly rejected without auth")
            else:
                print(f"❌ Unexpected admin response: {response_data}")
            
            # Test 4: Try authentication (will fail unless you have valid creds)
            print("\n🔐 Testing authentication...")
            auth_request = {
                "id": "test-auth-1",
                "type": "auth",
                "data": {
                    "username": "test_user",
                    "password": "test_password"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(auth_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('success'):
                print("✅ Authentication successful!")
                
                # Test authenticated admin request
                print("\n🔑 Testing admin request with auth...")
                await websocket.send(json.dumps(admin_request))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get('success'):
                    print(f"✅ Authenticated admin request successful: {response_data.get('data', {}).get('message')}")
                else:
                    print(f"❌ Authenticated admin request failed: {response_data}")
            else:
                print(f"ℹ️ Authentication failed (expected with test credentials): {response_data.get('error')}")
            
            print("\n🎉 WebSocket test completed!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    return True


async def main():
    """Main test function."""
    print("🚀 Pileup Buster WebSocket Test Client")
    print("=" * 50)
    
    success = await test_websocket_connection()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
