#!/usr/bin/env python3
"""
Test WebSocket Authentication
"""

import asyncio
import websockets
import json
import os
from pathlib import Path

async def test_admin_operation(websocket, session_token):
    """Test an admin operation with the session token"""
    print(f"\n🔧 Testing admin operation with token...")
    
    # Test getting the queue
    admin_request = {
        "type": "admin_get_queue",
        "request_id": "test_admin_001",
        "session_token": session_token
    }
    
    print(f"📤 Sending admin request: {json.dumps(admin_request, indent=2)}")
    await websocket.send(json.dumps(admin_request))
    
    try:
        admin_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        print(f"📨 Received admin response: {admin_response}")
        
        admin_data = json.loads(admin_response)
        print(f"📥 Parsed admin response:")
        print(json.dumps(admin_data, indent=2))
        
        if admin_data.get("type") == "admin_get_queue_response":
            print("✅ Admin operation successful!")
            queue_items = admin_data.get("queue", [])
            print(f"📋 Queue has {len(queue_items)} items")
        else:
            print(f"❌ Unexpected admin response type: {admin_data.get('type', 'Unknown')}")
            
    except asyncio.TimeoutError:
        print("❌ No admin response received within 5 seconds")

async def test_websocket_auth():
    """Test WebSocket authentication flow"""
    
    # Load admin credentials from environment
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'Letmein!')
    
    print(f"Testing WebSocket authentication...")
    print(f"Username: {admin_username}")
    print(f"Password: {'*' * len(admin_password)}")
    print(f"Expected password: Letmein!")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/api/ws"
        print(f"\nConnecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")
            
            # Receive welcome message
            try:
                welcome_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Raw welcome message: {welcome_message}")
                
                welcome_data = json.loads(welcome_message)
                print(f"📥 Parsed welcome data:")
                print(json.dumps(welcome_data, indent=2))
                
                if welcome_data.get("type") == "welcome":
                    print("✅ Welcome message received correctly")
                else:
                    print(f"❌ Unexpected welcome message format: {welcome_data}")
                    
            except asyncio.TimeoutError:
                print("❌ No welcome message received within 5 seconds")
                return
            
            # Send authentication request
            auth_request = {
                "type": "auth_request",
                "request_id": "test_auth_001",
                "username": admin_username,
                "password": admin_password
            }
            
            print(f"\n📤 Sending auth request: {json.dumps(auth_request, indent=2)}")
            await websocket.send(json.dumps(auth_request))
            print("✅ Auth request sent successfully")
            
            # Wait for authentication response
            try:
                print("\n⏳ Waiting for auth response (10 second timeout)...")
                auth_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📨 Raw auth response: {auth_response}")
                
                auth_data = json.loads(auth_response)
                print(f"📥 Parsed response data:")
                print(json.dumps(auth_data, indent=2))
                
                if auth_data.get("type") == "auth_response":
                    if auth_data.get("authenticated"):
                        print("✅ Authentication successful!")
                        print(f"🔑 Token: {auth_data.get('session_token', 'N/A')}")
                        print(f"⏰ Expires: {auth_data.get('expires_at', 'N/A')}")
                        
                        # Test an admin operation with the token
                        await test_admin_operation(websocket, auth_data.get('session_token'))
                        
                    else:
                        print(f"❌ Authentication failed: {auth_data.get('message', 'Unknown error')}")
                        print("❓ Check if the credentials match the .env file")
                else:
                    print(f"❌ Unexpected response type: {auth_data.get('type', 'Unknown')}")
                    print(f"Full response: {auth_data}")
                    
            except asyncio.TimeoutError:
                print("❌ No auth response received within 10 seconds")
                print("❌ Server is not processing auth requests!")
                return
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_auth())
