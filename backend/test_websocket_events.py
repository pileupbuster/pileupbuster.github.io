#!/usr/bin/env python3
"""
WebSocket Event Integration Test

This script tests the Phase 5 event integration to ensure WebSocket clients
receive real-time events when operations are performed.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import websockets
import uuid
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebSocketEventTestClient:
    """Test client for WebSocket event integration."""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws/connect"):
        self.uri = uri
        self.websocket = None
        self.authenticated = False
        self.received_events = []
        self.listening_for_events = False
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to WebSocket server at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket server")
    
    async def send_message(self, message_type: str, operation: str = None, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Send a message and wait for response."""
        if not self.websocket:
            logger.error("Not connected to WebSocket server")
            return None
        
        message_id = str(uuid.uuid4())
        
        # Build message based on type
        if message_type == "request":
            message = {
                "type": "request",
                "id": message_id,
                "operation": operation,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        elif message_type == "auth":
            message = {
                "type": "auth",
                "id": message_id,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"Unknown message type: {message_type}")
            return None
        
        try:
            # Send message
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent {message_type} message: {operation or message_type}")
            
            # Wait for response (not event)
            while True:
                response_text = await self.websocket.recv()
                response = json.loads(response_text)
                
                # Check if this is the response we're waiting for
                if response.get("type") == "response" and response.get("id") == message_id:
                    return response
                elif response.get("type") == "response" and response.get("operation") == "auth" and response.get("id") == message_id:
                    return response
                elif response.get("type") == "event":
                    # This is an event, store it and continue waiting
                    self.received_events.append(response)
                    logger.info(f"📡 Received event: {response.get('event')} - {response.get('data', {}).get('message', 'No message')}")
                else:
                    # Some other message type, ignore and continue
                    logger.debug(f"Received non-response message: {response.get('type')}")
                    
        except Exception as e:
            logger.error(f"Error sending/receiving message: {e}")
            return None
    
    async def listen_for_events(self, duration: int = 10):
        """Listen for events for a specific duration."""
        logger.info(f"🎧 Listening for events for {duration} seconds...")
        self.listening_for_events = True
        self.received_events = []
        
        try:
            # Set a timeout for listening
            async with asyncio.timeout(duration):
                while self.listening_for_events:
                    try:
                        message_text = await self.websocket.recv()
                        message = json.loads(message_text)
                        
                        if message.get("type") == "event":
                            self.received_events.append(message)
                            event_type = message.get("event")
                            event_data = message.get("data", {})
                            logger.info(f"📡 Event received: {event_type}")
                            
                            # Log specific event details
                            if event_type == "queue_update":
                                queue_size = event_data.get("total", 0)
                                logger.info(f"   Queue size: {queue_size}")
                            elif event_type == "frequency_update":
                                frequency = event_data.get("frequency")
                                logger.info(f"   Frequency: {frequency}")
                            elif event_type == "system_status":
                                active = event_data.get("active")
                                logger.info(f"   System active: {active}")
                                
                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        logger.error(f"Error receiving event: {e}")
                        break
                        
        except asyncio.TimeoutError:
            logger.info("🕐 Event listening timeout reached")
        
        self.listening_for_events = False
        logger.info(f"📊 Total events received: {len(self.received_events)}")
        return self.received_events
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with the server."""
        response = await self.send_message("auth", data={
            "username": username,
            "password": password
        })
        
        if response and response.get("success"):
            self.authenticated = True
            logger.info("✅ Authentication successful")
            return True
        else:
            logger.error(f"❌ Authentication failed: {response}")
            return False
    
    async def trigger_queue_event(self):
        """Trigger a queue event by registering a callsign."""
        logger.info("🎯 Triggering queue event by registering callsign...")
        response = await self.send_message("request", "queue.register", {"callsign": "TEST123"})
        
        if response and response.get("success"):
            logger.info("✅ Callsign registered successfully")
            return True
        else:
            logger.info(f"ℹ️  Registration response: {response.get('error', 'Unknown error')}")
            return False
    
    async def trigger_frequency_event(self):
        """Trigger a frequency event (requires authentication)."""
        if not self.authenticated:
            logger.warning("⚠️  Cannot trigger frequency event - not authenticated")
            return False
            
        logger.info("🎯 Triggering frequency event...")
        response = await self.send_message("request", "admin.set_frequency", {"frequency": "14.205.00"})
        
        if response and response.get("success"):
            logger.info("✅ Frequency set successfully")
            return True
        else:
            logger.error(f"❌ Failed to set frequency: {response}")
            return False


async def test_event_integration():
    """Test the event integration functionality."""
    logger.info("🚀 Starting WebSocket Event Integration Test (Phase 5)")
    
    client = WebSocketEventTestClient()
    
    # Connect to server
    if not await client.connect():
        logger.error("Cannot connect to WebSocket server. Make sure the server is running.")
        return False
    
    try:
        # Consume welcome event
        welcome_text = await client.websocket.recv()
        welcome = json.loads(welcome_text)
        logger.info(f"📨 Welcome event: {welcome.get('event')} - Events enabled: {welcome.get('data', {}).get('events_enabled', False)}")
        
        # Test 1: Listen for existing events
        logger.info("\n🧪 Test 1: Listen for background events")
        await client.listen_for_events(3)
        
        # Test 2: Trigger a queue event and listen
        logger.info("\n🧪 Test 2: Trigger queue event and listen")
        
        # Start listening in background
        listen_task = asyncio.create_task(client.listen_for_events(5))
        
        # Wait a moment then trigger event
        await asyncio.sleep(1)
        await client.trigger_queue_event()
        
        # Wait for listening to complete
        events = await listen_task
        
        # Check if we received a queue_update event
        queue_events = [e for e in events if e.get("event") == "queue_update"]
        if queue_events:
            logger.info("✅ Queue update event received successfully!")
        else:
            logger.warning("⚠️  No queue update event received")
        
        # Test 3: Test admin events (if credentials provided)
        logger.info("\n🧪 Test 3: Test admin events")
        
        # Try to authenticate
        if await client.authenticate("admin", "Letmein!"):
            # Start listening for admin events
            listen_task = asyncio.create_task(client.listen_for_events(5))
            
            # Wait a moment then trigger frequency event
            await asyncio.sleep(1)
            await client.trigger_frequency_event()
            
            # Wait for listening to complete
            admin_events = await listen_task
            
            # Check if we received frequency_update event
            frequency_events = [e for e in admin_events if e.get("event") == "frequency_update"]
            if frequency_events:
                logger.info("✅ Frequency update event received successfully!")
            else:
                logger.warning("⚠️  No frequency update event received")
        
        # Summary
        total_events = len(client.received_events)
        event_types = set(e.get("event") for e in client.received_events)
        
        logger.info(f"\n📊 Event Integration Test Summary:")
        logger.info(f"   Total events received: {total_events}")
        logger.info(f"   Event types: {list(event_types)}")
        
        if total_events > 0:
            logger.info("🎉 Phase 5 Event Integration: SUCCESS!")
            return True
        else:
            logger.warning("⚠️  Phase 5 Event Integration: No events received")
            return False
            
    finally:
        await client.disconnect()


def main():
    """Main entry point."""
    success = asyncio.run(test_event_integration())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
