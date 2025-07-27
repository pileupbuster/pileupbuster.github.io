#!/usr/bin/env python3
"""
Quick test to verify WebSocket heartbeat is working
"""

import asyncio
import websockets
import json
import time

async def quick_heartbeat_test():
    """Quick test for heartbeat functionality"""
    print("🔌 Quick Heartbeat Test")
    print("=" * 40)
    
    try:
        # Connect and authenticate
        websocket = await websockets.connect("ws://localhost:8000/api/ws")
        print("✅ Connected")
        
        # Skip welcome
        await websocket.recv()
        
        # Authenticate
        auth = {
            "type": "auth_request", 
            "request_id": "test_auth",
            "username": "admin", 
            "password": "Letmein!"
        }
        await websocket.send(json.dumps(auth))
        
        auth_response = await websocket.recv()
        auth_data = json.loads(auth_response)
        
        if auth_data.get("authenticated"):
            print("✅ Authenticated")
            
            # Wait for heartbeat (should come at 30 seconds)
            print("💓 Waiting for heartbeat...")
            start_time = time.time()
            
            while time.time() - start_time < 35:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "ping" and data.get("heartbeat"):
                        elapsed = time.time() - start_time
                        print(f"✅ Heartbeat received at {elapsed:.1f}s!")
                        print(f"   Server initiated: {data.get('server_initiated')}")
                        print(f"   Heartbeat flag: {data.get('heartbeat')}")
                        await websocket.close()
                        return True
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"⏰ Still waiting... {elapsed:.1f}s")
                    
            print("❌ No heartbeat received within 35 seconds")
            await websocket.close()
            return False
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    success = await quick_heartbeat_test()
    print("\n" + "=" * 40)
    if success:
        print("🎉 Heartbeat is working!")
    else:
        print("❌ Heartbeat test failed")

if __name__ == "__main__":
    asyncio.run(main())
