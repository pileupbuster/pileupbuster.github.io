#!/usr/bin/env python3
"""
Test script to verify WebSocket heartbeat functionality for authenticated clients
"""

import asyncio
import websockets
import json
import time

# Configuration
WS_URL = "ws://localhost:8000/api/ws"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Letmein!"

class HeartbeatTest:
    def __init__(self):
        self.websocket = None
        self.session_token = None
        self.heartbeat_count = 0
        self.test_duration = 70  # Test for 70 seconds (2+ heartbeat cycles)
        
    async def test_heartbeat_functionality(self):
        """Test that authenticated clients receive server-initiated heartbeats"""
        print("� Testing WebSocket Heartbeat for Authenticated Clients")
        print("=" * 60)
        
        try:
            # Connect to WebSocket
            self.websocket = await websockets.connect(WS_URL)
            print("✅ Connected to WebSocket")
            
            # Skip welcome message
            welcome = await self.websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📡 Welcome: {welcome_data.get('message')}")
            
            # Authenticate
            print("\n� Authenticating...")
            auth_request = {
                "type": "auth_request",
                "request_id": f"auth_{int(time.time() * 1000)}",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            await self.websocket.send(json.dumps(auth_request))
            auth_response = await self.websocket.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get("type") == "auth_response" and auth_data.get("authenticated"):
                self.session_token = auth_data.get("session_token")
                print("✅ Authentication successful")
                print(f"🎫 Session token: {self.session_token[:20]}...")
            else:
                print(f"❌ Authentication failed: {auth_data}")
                return False
                
            # Now listen for heartbeat messages
            print(f"\n💓 Listening for server heartbeats for {self.test_duration} seconds...")
            print("Expected: Server should send 'ping' messages every 30 seconds to authenticated clients")
            print("-" * 60)
            
            start_time = time.time()
            last_heartbeat_time = start_time
            
            while time.time() - start_time < self.test_duration:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    message_type = data.get("type")
                    
                    if message_type == "ping":
                        self.heartbeat_count += 1
                        time_since_last = current_time - last_heartbeat_time
                        server_initiated = data.get("server_initiated", False)
                        heartbeat = data.get("heartbeat", False)
                        
                        print(f"💓 [{elapsed:5.1f}s] Heartbeat #{self.heartbeat_count} received")
                        print(f"   Time since last: {time_since_last:.1f}s")
                        print(f"   Server initiated: {server_initiated}")
                        print(f"   Heartbeat flag: {heartbeat}")
                        
                        last_heartbeat_time = current_time
                        
                        # Optionally respond with pong
                        pong_response = {
                            "type": "pong",
                            "timestamp": time.time()
                        }
                        await self.websocket.send(json.dumps(pong_response))
                        print(f"   ↳ Sent pong response")
                        print()
                        
                    else:
                        elapsed = time.time() - start_time
                        print(f"� [{elapsed:5.1f}s] Other message: {message_type}")
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"⏰ [{elapsed:5.1f}s] Waiting for heartbeat...")
                    continue
                    
            print("-" * 60)
            print("📊 Test Results:")
            print(f"   Duration: {self.test_duration} seconds")
            print(f"   Heartbeats received: {self.heartbeat_count}")
            print(f"   Expected heartbeats: ~{self.test_duration // 30}")
            
            if self.heartbeat_count >= 2:
                print("✅ SUCCESS: Server is sending heartbeats to authenticated clients!")
                return True
            elif self.heartbeat_count > 0:
                print("⚠️ PARTIAL: Some heartbeats received, but fewer than expected")
                return True
            else:
                print("❌ FAILURE: No heartbeats received from server")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        finally:
            if self.websocket:
                await self.websocket.close()

async def main():
    """Run heartbeat test"""
    print("🧪 WebSocket Heartbeat Testing")
    print("Testing server-initiated heartbeats for authenticated clients")
    print("=" * 70)
    
    tester = HeartbeatTest()
    success = await tester.test_heartbeat_functionality()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Heartbeat test PASSED")
        print("💓 Server correctly sends heartbeats to authenticated clients")
    else:
        print("❌ Heartbeat test FAILED")
        print("⚠️ Check server heartbeat implementation")

if __name__ == "__main__":
    asyncio.run(main())
