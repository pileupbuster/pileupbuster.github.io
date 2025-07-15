import asyncio
import websockets
import json
from datetime import datetime

async def handle_client(websocket):
    print(f"📡 New WebSocket connection from {websocket.remote_address}")
    
    try:
        # Send welcome message
        welcome = {
            "type": "welcome",
            "message": "Test WebSocket server connected",
            "server_time": datetime.now().timestamp()
        }
        await websocket.send(json.dumps(welcome))
        print(f"📤 Sent welcome: {welcome}")
        
        async for message in websocket:
            print(f"📥 Received message: {message}")
            
            try:
                # Parse the message
                data = json.loads(message)
                print(f"📋 Parsed JSON: {json.dumps(data, indent=2)}")
                
                # Check if this is a QSO start message
                if data.get("type") == "qso_start":
                    print("🎉 QSO START MESSAGE DETECTED!")
                    print(f"   Callsign: {data.get('data', {}).get('callsign')}")
                    print(f"   Frequency: {data.get('data', {}).get('frequency_mhz')}")
                    print(f"   Mode: {data.get('data', {}).get('mode')}")
                    print(f"   Source: {data.get('data', {}).get('source')}")
                    print(f"   Triggered by: {data.get('data', {}).get('triggered_by')}")
                    
                    # Send acknowledgment
                    ack = {
                        "type": "ack",
                        "timestamp": datetime.now().isoformat(),
                        "received": data
                    }
                    await websocket.send(json.dumps(ack))
                    print(f"📤 Sent acknowledgment: {ack}")
                
                elif data.get("type") == "ping":
                    # Respond to ping
                    pong = {"type": "pong", "timestamp": datetime.now().isoformat()}
                    await websocket.send(json.dumps(pong))
                    print(f"📤 Sent pong: {pong}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   Raw message: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        print("🔌 WebSocket connection closed")
    except Exception as e:
        print(f"❌ Error handling WebSocket: {e}")

async def main():
    print("🚀 Starting WebSocket test server on localhost:8765...")
    print("📱 This server will:")
    print("   - Accept WebSocket connections on ws://localhost:8765")
    print("   - Log all incoming messages")
    print("   - Send acknowledgments for QSO messages")
    print("   - Help debug your logging software integration")
    print()
    
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("✅ WebSocket server started successfully!")
    print("💡 Send a test message from your logging software now...")
    print("🔍 Or use the test page to send a test QSO message")
    print()
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
