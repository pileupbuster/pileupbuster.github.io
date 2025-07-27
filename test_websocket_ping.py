#!/usr/bin/env python3
"""
Simple WebSocket ping test script using the existing test_websocket_client infrastructure
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_admin_ping():
    """Test the WebSocket admin ping endpoint"""
    print("🏓 Testing WebSocket Admin Ping Endpoint...")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/api/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Receive welcome message
            welcome_raw = await websocket.recv()
            welcome = json.loads(welcome_raw)
            print(f"📩 Welcome: {welcome.get('message')}")
            
            # Authenticate
            auth_request = {
                "type": "auth_request",
                "request_id": "auth_001",
                "username": "admin",
                "password": "Letmein!"
            }
            
            await websocket.send(json.dumps(auth_request))
            auth_response_raw = await websocket.recv()
            auth_response = json.loads(auth_response_raw)
            
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
            await websocket.send(json.dumps(ping_request))
            
            # Receive pong response
            pong_response_raw = await websocket.recv()
            pong_response = json.loads(pong_response_raw)
            
            if pong_response.get('type') == 'success' and pong_response.get('message') == 'pong':
                print(f"✅ WebSocket Admin Ping successful!")
                print(f"   Message: {pong_response.get('message')}")
                print(f"   Request ID: {pong_response.get('request_id')}")
                data = pong_response.get('data', {})
                print(f"   Server Time: {data.get('server_time')}")
                print(f"   Authenticated: {data.get('authenticated')}")
                print(f"   Ping Type: {data.get('ping_type')}")
                print(f"   Full Response: {pong_response}")
                return True
            else:
                print(f"❌ WebSocket Admin Ping failed")
                print(f"   Response: {pong_response}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket Admin Ping error: {e}")
        return False

async def test_websocket_public_ping():
    """Test the WebSocket public ping endpoint"""
    print("\n🏓 Testing WebSocket Public Ping Endpoint...")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/api/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Receive welcome message
            welcome_raw = await websocket.recv()
            welcome = json.loads(welcome_raw)
            print(f"📩 Welcome: {welcome.get('message')}")
            
            # Send public ping (no authentication)
            ping_request = {
                "type": "ping",
                "request_id": "public_ping_001"
            }
            
            print("📤 Sending public ping...")
            await websocket.send(json.dumps(ping_request))
            
            # Receive pong response
            pong_response_raw = await websocket.recv()
            pong_response = json.loads(pong_response_raw)
            
            if pong_response.get('type') == 'pong':
                print(f"✅ WebSocket Public Ping successful!")
                print(f"   Type: {pong_response.get('type')}")
                print(f"   Timestamp: {pong_response.get('timestamp')}")
                print(f"   Full Response: {pong_response}")
                return True
            else:
                print(f"❌ WebSocket Public Ping failed")
                print(f"   Response: {pong_response}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket Public Ping error: {e}")
        return False

async def main():
    print("🧪 Testing WebSocket Ping Endpoints")
    print("=" * 50)
    
    # Test WebSocket ping endpoints
    admin_success = await test_websocket_admin_ping()
    public_success = await test_websocket_public_ping()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   WebSocket Admin Ping: {'✅ PASS' if admin_success else '❌ FAIL'}")
    print(f"   WebSocket Public Ping: {'✅ PASS' if public_success else '❌ FAIL'}")
    
    if all([admin_success, public_success]):
        print("\n🎉 All WebSocket ping endpoints working correctly!")
    else:
        print("\n⚠️  Some WebSocket ping endpoints failed")

if __name__ == "__main__":
    asyncio.run(main())
