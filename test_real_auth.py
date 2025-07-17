#!/usr/bin/env python3
"""
WebSocket Authentication Test

Test WebSocket with real admin credentials from environment.
"""

import asyncio
import json
import websockets
import os
from dotenv import load_dotenv
from datetime import datetime


async def test_real_auth():
    """Test WebSocket with real admin credentials."""
    
    # Load environment variables from backend directory
    load_dotenv('backend/.env')
    
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', '')
    
    if not admin_password:
        print("❌ ADMIN_PASSWORD not found in environment variables")
        return False
    
    uri = "ws://localhost:8000/ws/connect"
    print(f"🔐 Testing WebSocket authentication with real credentials...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for welcome message
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                print(f"📨 Welcome: {welcome_data.get('data', {}).get('message')}")
            except asyncio.TimeoutError:
                print("⏰ No welcome message received")
            
            # Test authentication with real credentials
            print(f"\n🔑 Testing authentication with username: {admin_username}")
            auth_request = {
                "id": "real-auth-test",
                "type": "auth",
                "data": {
                    "username": admin_username,
                    "password": admin_password
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(auth_request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('success'):
                print("✅ Authentication successful!")
                print(f"   User type: {response_data.get('data', {}).get('user_type')}")
                
                # Test authenticated admin request
                print("\n🔑 Testing authenticated admin request...")
                admin_request = {
                    "id": "real-admin-test",
                    "type": "request",
                    "operation": "admin.get_queue",
                    "data": {},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(admin_request))
                admin_response = await websocket.recv()
                admin_data = json.loads(admin_response)
                
                if admin_data.get('success'):
                    print(f"✅ Admin request successful: {admin_data.get('data', {}).get('message')}")
                else:
                    print(f"❌ Admin request failed: {admin_data}")
                
                return True
            else:
                print(f"❌ Authentication failed: {response_data.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    print("🔐 WebSocket Real Authentication Test")
    print("=" * 40)
    
    success = await test_real_auth()
    
    if success:
        print("\n✅ Real authentication test passed!")
    else:
        print("\n❌ Real authentication test failed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
