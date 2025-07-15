import asyncio
import websockets
import json
import logging
from datetime import datetime
import signal
import sys
from typing import Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PileupBusterWebSocketServer:
    def __init__(self):
        self.frontend_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.logging_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        
    async def register_client(self, websocket, client_type="unknown"):
        """Register a new client connection"""
        if client_type == "frontend":
            self.frontend_clients.add(websocket)
            logger.info(f"📱 Frontend client connected from {websocket.remote_address}")
        elif client_type == "logging":
            self.logging_clients.add(websocket)
            logger.info(f"📻 Logging software connected from {websocket.remote_address}")
        else:
            # Try to determine client type from first message
            logger.info(f"🔍 Unknown client connected from {websocket.remote_address}")
            
        # Send welcome message
        welcome = {
            "type": "welcome",
            "message": f"Connected to Pileup Buster WebSocket Server as {client_type}",
            "server_time": datetime.now().timestamp()
        }
        await websocket.send(json.dumps(welcome))
        
    async def unregister_client(self, websocket):
        """Remove client from all sets"""
        self.frontend_clients.discard(websocket)
        self.logging_clients.discard(websocket)
        logger.info(f"🔌 Client disconnected from {websocket.remote_address}")
        
    async def broadcast_to_frontends(self, message):
        """Send message to all connected frontend clients"""
        if not self.frontend_clients:
            logger.warning("📭 No frontend clients connected to receive message")
            return
            
        disconnected = set()
        for client in self.frontend_clients:
            try:
                await client.send(json.dumps(message))
                logger.info(f"📤 Sent to frontend {client.remote_address}: {message['type']}")
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"❌ Error sending to frontend {client.remote_address}: {e}")
                disconnected.add(client)
                
        # Clean up disconnected clients
        for client in disconnected:
            self.frontend_clients.discard(client)
            
    async def handle_logging_message(self, websocket, message):
        """Handle messages from logging software"""
        try:
            data = json.loads(message)
            logger.info(f"📻 Received from logging software: {data.get('type', 'unknown')}")
            
            if data.get("type") == "qso_start":
                logger.info("🎉 QSO START MESSAGE DETECTED!")
                qso_data = data.get("data", {})
                logger.info(f"   Callsign: {qso_data.get('callsign')}")
                logger.info(f"   Frequency: {qso_data.get('frequency_mhz')}")
                logger.info(f"   Mode: {qso_data.get('mode')}")
                logger.info(f"   Source: {qso_data.get('source')}")
                logger.info(f"   Triggered by: {qso_data.get('triggered_by')}")
                
                # Forward to all frontend clients
                await self.broadcast_to_frontends(data)
                
                # Send acknowledgment back to logging software
                ack = {
                    "type": "ack",
                    "timestamp": datetime.now().isoformat(),
                    "received": data
                }
                await websocket.send(json.dumps(ack))
                logger.info("📤 Sent acknowledgment to logging software")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error from logging software: {e}")
        except Exception as e:
            logger.error(f"❌ Error handling logging message: {e}")
            
    async def handle_frontend_message(self, websocket, message):
        """Handle messages from frontend clients"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")
            logger.info(f"📱 Frontend message: {msg_type}")
            
            if msg_type == "ping":
                # Respond to ping
                pong = {"type": "pong", "timestamp": datetime.now().isoformat()}
                await websocket.send(json.dumps(pong))
                logger.info("📤 Sent pong to frontend")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error from frontend: {e}")
        except Exception as e:
            logger.error(f"❌ Error handling frontend message: {e}")
            
    async def determine_client_type(self, websocket, first_message):
        """Try to determine if this is a frontend or logging client"""
        try:
            data = json.loads(first_message)
            msg_type = data.get("type", "")
            
            # Logging software typically sends qso_start messages
            if msg_type == "qso_start" or data.get("data", {}).get("source") == "pblog_native":
                return "logging"
            # Frontend typically sends ping messages
            elif msg_type == "ping":
                return "frontend"
            else:
                # Default to frontend for unknown messages
                return "frontend"
                
        except json.JSONDecodeError:
            # If not JSON, assume it's frontend
            return "frontend"
            
    async def handle_client(self, websocket):
        """Handle a new WebSocket client connection"""
        client_type = None
        try:
            # Wait for first message to determine client type
            first_message = await websocket.recv()
            client_type = await self.determine_client_type(websocket, first_message)
            
            # Register client
            await self.register_client(websocket, client_type)
            
            # Handle the first message
            if client_type == "logging":
                await self.handle_logging_message(websocket, first_message)
            else:
                await self.handle_frontend_message(websocket, first_message)
            
            # Handle subsequent messages
            async for message in websocket:
                if client_type == "logging":
                    await self.handle_logging_message(websocket, message)
                else:
                    await self.handle_frontend_message(websocket, message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client {websocket.remote_address} disconnected")
        except Exception as e:
            logger.error(f"❌ Error handling client {websocket.remote_address}: {e}")
        finally:
            await self.unregister_client(websocket)
            
    async def start_server(self, host="localhost", port=8765):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting Pileup Buster WebSocket Server on {host}:{port}")
        logger.info("📱 Frontend clients should connect to: ws://localhost:8765")
        logger.info("📻 Logging software should send messages to: ws://localhost:8765")
        logger.info("🔄 Server will forward QSO messages from logging software to frontend")
        
        self.running = True
        server = await websockets.serve(self.handle_client, host, port)
        logger.info("✅ WebSocket server started successfully!")
        
        return server

# Global server instance
server_instance = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Shutdown signal received")
    if server_instance:
        server_instance.running = False
    sys.exit(0)

async def main():
    global server_instance
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server_instance = PileupBusterWebSocketServer()
    server = await server_instance.start_server()
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
