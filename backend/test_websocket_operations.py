#!/usr/bin/env python3
"""
WebSocket Operations Test Client

This script tests all WebSocket operations to ensure they work correctly.
It provides a comprehensive test suite for the Phase 4 implementation.
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


class WebSocketTestClient:
    """Test client for WebSocket operations."""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws/connect"):
        self.uri = uri
        self.websocket = None
        self.authenticated = False
    
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
        elif message_type == "ping":
            message = {
                "type": "ping",
                "id": message_id,
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
            
            # Wait for response
            response_text = await self.websocket.recv()
            response = json.loads(response_text)
            
            logger.info(f"Received response: {response.get('type', 'unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Error sending/receiving message: {e}")
            return None
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with the server."""
        response = await self.send_message("auth", data={
            "username": username,
            "password": password
        })
        
        if response and response.get("success"):
            self.authenticated = True
            logger.info("Authentication successful")
            return True
        else:
            logger.error(f"Authentication failed: {response}")
            return False
    
    async def test_ping(self) -> bool:
        """Test ping/pong functionality."""
        logger.info("Testing ping/pong...")
        response = await self.send_message("ping")
        
        if response and response.get("type") == "pong":
            logger.info("✓ Ping/pong test passed")
            return True
        else:
            logger.error(f"✗ Ping/pong test failed: {response}")
            return False
    
    async def test_public_operations(self) -> bool:
        """Test all public operations."""
        logger.info("Testing public operations...")
        tests_passed = 0
        total_tests = 3
        
        # Test public.get_status
        response = await self.send_message("request", "public.get_status")
        if response and response.get("success"):
            logger.info("✓ public.get_status test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ public.get_status test failed: {response}")
        
        # Test public.get_frequency
        response = await self.send_message("request", "public.get_frequency")
        if response and response.get("success"):
            logger.info("✓ public.get_frequency test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ public.get_frequency test failed: {response}")
        
        # Test public.get_split
        response = await self.send_message("request", "public.get_split")
        if response and response.get("success"):
            logger.info("✓ public.get_split test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ public.get_split test failed: {response}")
        
        success = tests_passed == total_tests
        logger.info(f"Public operations: {tests_passed}/{total_tests} passed")
        return success
    
    async def test_queue_operations(self) -> bool:
        """Test queue operations."""
        logger.info("Testing queue operations...")
        tests_passed = 0
        total_tests = 3
        
        # Test queue.list
        response = await self.send_message("request", "queue.list")
        if response and response.get("success"):
            logger.info("✓ queue.list test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ queue.list test failed: {response}")
        
        # Test queue.register (will likely fail if system is inactive, but should return proper error)
        response = await self.send_message("request", "queue.register", {"callsign": "W1AW"})
        if response:
            if response.get("success"):
                logger.info("✓ queue.register test passed (system active)")
                tests_passed += 1
            elif "inactive" in response.get("error", "").lower():
                logger.info("✓ queue.register test passed (system inactive - expected error)")
                tests_passed += 1
            else:
                logger.error(f"✗ queue.register test failed: {response}")
        else:
            logger.error("✗ queue.register test failed: no response")
        
        # Test queue.get_status
        response = await self.send_message("request", "queue.get_status", {"callsign": "W1AW"})
        if response:
            # This should fail if callsign not in queue, which is expected
            if not response.get("success") and "not found" in response.get("error", "").lower():
                logger.info("✓ queue.get_status test passed (callsign not found - expected)")
                tests_passed += 1
            elif response.get("success"):
                logger.info("✓ queue.get_status test passed (callsign found)")
                tests_passed += 1
            else:
                logger.error(f"✗ queue.get_status test failed: {response}")
        else:
            logger.error("✗ queue.get_status test failed: no response")
        
        success = tests_passed == total_tests
        logger.info(f"Queue operations: {tests_passed}/{total_tests} passed")
        return success
    
    async def test_system_operations(self) -> bool:
        """Test system operations."""
        logger.info("Testing system operations...")
        tests_passed = 0
        total_tests = 3
        
        # Test system.ping
        response = await self.send_message("request", "system.ping")
        if response and response.get("success"):
            logger.info("✓ system.ping test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ system.ping test failed: {response}")
        
        # Test system.heartbeat
        response = await self.send_message("request", "system.heartbeat")
        if response and response.get("success"):
            logger.info("✓ system.heartbeat test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ system.heartbeat test failed: {response}")
        
        # Test system.info
        response = await self.send_message("request", "system.info")
        if response and response.get("success"):
            logger.info("✓ system.info test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ system.info test failed: {response}")
        
        success = tests_passed == total_tests
        logger.info(f"System operations: {tests_passed}/{total_tests} passed")
        return success
    
    async def test_admin_operations(self, username: str, password: str) -> bool:
        """Test admin operations (requires authentication)."""
        logger.info("Testing admin operations...")
        
        # First authenticate
        if not await self.authenticate(username, password):
            logger.error("Cannot test admin operations - authentication failed")
            return False
        
        tests_passed = 0
        total_tests = 3
        
        # Test admin.get_queue
        response = await self.send_message("request", "admin.get_queue")
        if response and response.get("success"):
            logger.info("✓ admin.get_queue test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ admin.get_queue test failed: {response}")
        
        # Test admin.get_system_status
        response = await self.send_message("request", "admin.get_system_status")
        if response and response.get("success"):
            logger.info("✓ admin.get_system_status test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ admin.get_system_status test failed: {response}")
        
        # Test admin.set_frequency
        response = await self.send_message("request", "admin.set_frequency", {"frequency": "14.205.00"})
        if response and response.get("success"):
            logger.info("✓ admin.set_frequency test passed")
            tests_passed += 1
        else:
            logger.error(f"✗ admin.set_frequency test failed: {response}")
        
        success = tests_passed == total_tests
        logger.info(f"Admin operations: {tests_passed}/{total_tests} passed")
        return success


async def run_tests():
    """Run all WebSocket tests."""
    logger.info("Starting WebSocket operations test suite...")
    
    client = WebSocketTestClient()
    
    # Connect to server
    if not await client.connect():
        logger.error("Cannot connect to WebSocket server. Make sure the server is running.")
        return False
    
    try:
        results = []
        
        # Test ping/pong
        results.append(await client.test_ping())
        
        # Test public operations
        results.append(await client.test_public_operations())
        
        # Test queue operations
        results.append(await client.test_queue_operations())
        
        # Test system operations
        results.append(await client.test_system_operations())
        
        # Test admin operations (you'll need to provide credentials)
        # Uncomment and provide real credentials to test admin operations
        # results.append(await client.test_admin_operations("your_username", "your_password"))
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        logger.info(f"\n=== TEST SUMMARY ===")
        logger.info(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            logger.info("🎉 All tests passed!")
            return True
        else:
            logger.warning("⚠️  Some tests failed")
            return False
            
    finally:
        await client.disconnect()


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        # Interactive mode for admin testing
        print("Enter admin credentials to test admin operations:")
        username = input("Username: ")
        password = input("Password: ")
        
        async def run_admin_tests():
            client = WebSocketTestClient()
            if await client.connect():
                try:
                    await client.test_admin_operations(username, password)
                finally:
                    await client.disconnect()
        
        asyncio.run(run_admin_tests())
    else:
        # Run standard test suite
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
