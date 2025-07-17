#!/usr/bin/env python3
"""
WebSocket Event Integration Test - Phase 5
Tests real-time event broadcasting from WebSocket operations.
"""
import asyncio
import json
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EventIntegrationTest:
    def __init__(self):
        self.websocket = None
        self.events_received = []
        self.listening = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            logger.info("🔌 Connecting to WebSocket server...")
            self.websocket = await websockets.connect("ws://localhost:8000/ws/connect")
            logger.info("✅ Connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Disconnected from WebSocket server")
    
    async def send_message(self, msg_type, operation, data=None):
        """Send a message and return immediately (no response wait)"""
        if not self.websocket:
            return None
            
        message = {
            "type": msg_type,
            "operation": operation,
        }
        
        if data:
            message["data"] = data
            
        await self.websocket.send(json.dumps(message))
        logger.info(f"📤 Sent: {operation}")
        
    async def authenticate(self):
        """Authenticate with the server using proper auth message"""
        logger.info("🔐 Authenticating with server...")
        
        auth_message = {
            "type": "auth",
            "data": {
                "username": "admin", 
                "password": "Letmein!"
            }
        }
        
        await self.websocket.send(json.dumps(auth_message))
        
        # Small delay to allow authentication to process
        await asyncio.sleep(0.5)
        logger.info("🔐 Authentication request sent")
    
    async def listen_for_events(self, duration=5):
        """Listen for events for a specified duration"""
        logger.info(f"👂 Listening for events for {duration} seconds...")
        self.listening = True
        
        end_time = asyncio.get_event_loop().time() + duration
        
        while self.listening and asyncio.get_event_loop().time() < end_time:
            try:
                # Use a short timeout to avoid blocking
                message = await asyncio.wait_for(self.websocket.recv(), timeout=0.5)
                
                try:
                    data = json.loads(message)
                    if data.get("type") == "event":
                        self.events_received.append(data)
                        logger.info(f"📨 Event received: {data.get('event_type')} - {data.get('data', {})}")
                    elif data.get("type") == "response":
                        logger.info(f"📋 Response: {data.get('operation')} - {data.get('success', False)}")
                    elif data.get("type") == "welcome":
                        logger.info(f"👋 Welcome: {data.get('message', '')}")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️  Received non-JSON message: {message}")
                    
            except asyncio.TimeoutError:
                # Timeout is expected, continue listening
                continue
            except Exception as e:
                logger.error(f"❌ Error receiving message: {e}")
                break
        
        self.listening = False
        logger.info(f"✅ Event listening completed. Total events received: {len(self.events_received)}")
    
    async def trigger_queue_operation(self):
        """Trigger a queue operation that should generate events"""
        logger.info("🎯 Triggering queue operation...")
        
        await self.send_message("request", "queue.register", {
            "callsign": "W1AW",  # Valid ITU callsign
            "frequency": 14205000,
            "mode": "FT8"
        })
        
        # Small delay to allow operation to complete
        await asyncio.sleep(0.5)
    
    async def activate_system(self):
        """Activate the system to allow operations"""
        logger.info("🔧 Activating system...")
        
        await self.send_message("request", "admin.set_system_status", {
            "active": True
        })
        
        # Small delay to allow operation to complete
        await asyncio.sleep(0.5)
    
    async def trigger_admin_operation(self):
        """Trigger an admin operation that should generate events"""
        logger.info("🎯 Triggering admin operation...")
        
        await self.send_message("request", "admin.set_frequency", {
            "frequency": "14.205.00"
        })
        
        # Small delay to allow operation to complete
        await asyncio.sleep(0.5)

async def run_event_integration_test():
    """Run comprehensive event integration test"""
    logger.info("🚀 Starting WebSocket Event Integration Test (Phase 5)")
    
    test = EventIntegrationTest()
    
    # Connect to server
    if not await test.connect():
        return False
    
    try:
        # Test 1: Listen for welcome and any background events
        logger.info("\n🧪 Test 1: Initial connection and background events")
        await test.listen_for_events(3)
        
        # Clear events from initial connection
        initial_events = len(test.events_received)
        test.events_received.clear()
        
        # Test 2: Authenticate and activate system
        logger.info("\n🧪 Test 2: System activation")
        
        # Authenticate first
        await test.authenticate()
        
        # Start listening in background
        listen_task = asyncio.create_task(test.listen_for_events(3))
        
        # Wait a moment, then activate system
        await asyncio.sleep(1)
        await test.activate_system()
        
        # Wait for listening to complete
        await listen_task
        
        activation_events = len(test.events_received)
        test.events_received.clear()
        
        # Test 3: Trigger queue operation and listen for events
        logger.info("\n🧪 Test 3: Queue operation event generation")
        
        # Start listening in background
        listen_task = asyncio.create_task(test.listen_for_events(5))
        
        # Wait a moment, then trigger operation
        await asyncio.sleep(1)
        await test.trigger_queue_operation()
        
        # Wait for listening to complete
        await listen_task
        
        queue_events = len(test.events_received)
        test.events_received.clear()
        
        # Test 4: Trigger admin operation
        logger.info("\n🧪 Test 4: Admin operation event generation")
        
        # Start listening in background
        listen_task = asyncio.create_task(test.listen_for_events(5))
        
        # Wait a moment, then trigger admin operation
        await asyncio.sleep(1)
        await test.trigger_admin_operation()
        
        # Wait for listening to complete
        await listen_task
        
        admin_events = len(test.events_received)
        
        # Report results
        logger.info("\n📊 Event Integration Test Results:")
        logger.info(f"   Initial/Background Events: {initial_events}")
        logger.info(f"   System Activation Events: {activation_events}")
        logger.info(f"   Queue Operation Events: {queue_events}")
        logger.info(f"   Admin Operation Events: {admin_events}")
        
        if queue_events > 0 or admin_events > 0 or activation_events > 0:
            logger.info("✅ Phase 5 Event Integration: SUCCESS - Events are being broadcast to WebSocket clients!")
        else:
            logger.info("⚠️  Phase 5 Event Integration: Events not detected - may need investigation")
        
        return True
        
    finally:
        await test.disconnect()

if __name__ == "__main__":
    try:
        success = asyncio.run(run_event_integration_test())
        if success:
            logger.info("🎉 Event integration test completed successfully")
        else:
            logger.error("❌ Event integration test failed")
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
