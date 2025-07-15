#!/usr/bin/env python3
"""
Ultra-simple WebSocket bridge: Logging Software -> Frontend
Just forwards QSO messages, nothing else.
"""
import asyncio
import websockets
import json

async def bridge():
    frontend_ws = None
    
    async def handle_logging_client(websocket, path):
        nonlocal frontend_ws
        print(f"📻 Logging software connected from {websocket.remote_address}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"📥 Received: {data.get('type', 'unknown')}")
                
                # Forward to frontend if connected
                if frontend_ws and not frontend_ws.closed:
                    await frontend_ws.send(message)
                    print(f"📤 Forwarded to frontend")
                    
                # Send ACK back to logging software
                if data.get('type') == 'qso_start':
                    ack = {"type": "ack", "timestamp": "now", "received": data}
                    await websocket.send(json.dumps(ack))
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Start server for logging software
    print("🚀 Starting bridge on localhost:8765")
    async with websockets.serve(handle_logging_client, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(bridge())
