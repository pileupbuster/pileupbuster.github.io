#!/usr/bin/env python3
"""
Quick WebSocket Test

Simple test to verify key operations are working.
"""

import asyncio
import json
import uuid
from datetime import datetime
import websockets

async def test_key_operations():
    """Test a few key WebSocket operations."""
    uri = "ws://localhost:8000/ws/connect"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket server")
        
        # Consume the welcome message
        welcome = await websocket.recv()
        print(f"📨 Welcome: {json.loads(welcome)['event']}")
        
        # Test system.info
        message = {
            "type": "request",
            "id": str(uuid.uuid4()),
            "operation": "system.info",
            "data": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send(json.dumps(message))
        response = json.loads(await websocket.recv())
        
        if response.get("success"):
            print("✅ system.info works!")
            print(f"   Server: {response['data']['server']}")
            print(f"   Operations: {len(response['data']['supported_operations'])} supported")
        else:
            print(f"❌ system.info failed: {response}")
        
        # Test queue.list
        message = {
            "type": "request", 
            "id": str(uuid.uuid4()),
            "operation": "queue.list",
            "data": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send(json.dumps(message))
        response = json.loads(await websocket.recv())
        
        if response.get("success"):
            queue_data = response['data']
            print(f"✅ queue.list works!")
            print(f"   Queue size: {queue_data['total']}")
            print(f"   System active: {queue_data['system_active']}")
        else:
            print(f"❌ queue.list failed: {response}")

if __name__ == "__main__":
    asyncio.run(test_key_operations())
