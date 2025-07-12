"""WebSocket server for QLog bridge"""
import asyncio
import websockets
import json
import logging
from typing import Set, Dict, Any, Optional
from websockets.exceptions import ConnectionClosed, WebSocketException
from config import BridgeConfig


logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for broadcasting QSO data to frontend clients"""
    
    def __init__(self, config: BridgeConfig):
        """
        Initialize WebSocket server
        
        Args:
            config: Bridge configuration
        """
        self.config = config
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
        
    async def start(self) -> bool:
        """
        Start WebSocket server
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("WebSocket server already running")
            return True
        
        try:
            # Start WebSocket server
            self.server = await websockets.serve(
                self._handle_client,
                "127.0.0.1",
                self.config.websocket_port,
                max_size=1024 * 1024,  # 1MB max message size
                ping_interval=30,      # Ping every 30 seconds
                ping_timeout=10,       # Wait 10 seconds for pong
                close_timeout=10       # Wait 10 seconds for close
            )
            
            self.running = True
            logger.info(f"WebSocket server started on port {self.config.websocket_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop WebSocket server"""
        self.running = False
        
        # Close all client connections
        if self.clients:
            logger.info(f"Closing {len(self.clients)} client connections")
            await asyncio.gather(
                *[client.close() for client in self.clients.copy()],
                return_exceptions=True
            )
            self.clients.clear()
        
        # Stop the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        
        logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str = "/") -> None:
        """Handle new WebSocket client connection"""
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New WebSocket client connected: {client_addr}")
        
        # Check client limit
        if len(self.clients) >= self.config.max_clients:
            logger.warning(f"Client limit reached, rejecting {client_addr}")
            await websocket.close(code=1013, reason="Server overloaded")
            return
        
        # Add client to set
        self.clients.add(websocket)
        
        try:
            # Send welcome message
            welcome_msg = {
                "type": "welcome",
                "message": "Connected to QLog Bridge",
                "server_time": asyncio.get_event_loop().time()
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {client_addr}: {message}")
                except Exception as e:
                    logger.error(f"Error handling message from {client_addr}: {e}")
                    
        except ConnectionClosed:
            logger.info(f"Client {client_addr} disconnected")
        except WebSocketException as e:
            logger.warning(f"WebSocket error with {client_addr}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with client {client_addr}: {e}")
        finally:
            # Remove client from set
            self.clients.discard(websocket)
            logger.debug(f"Client {client_addr} removed, {len(self.clients)} clients remaining")
    
    async def _handle_client_message(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """Handle message from WebSocket client"""
        msg_type = data.get("type")
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        if msg_type == "ping":
            # Respond to ping
            response = {"type": "pong", "timestamp": asyncio.get_event_loop().time()}
            await websocket.send(json.dumps(response))
            logger.debug(f"Responded to ping from {client_addr}")
            
        elif msg_type == "status":
            # Send server status
            status = self.get_status()
            response = {"type": "status", "data": status}
            await websocket.send(json.dumps(response))
            logger.debug(f"Sent status to {client_addr}")
            
        else:
            logger.warning(f"Unknown message type '{msg_type}' from {client_addr}")
    
    async def broadcast_qso(self, qso_data: Dict[str, Any]) -> None:
        """
        Broadcast QSO data to all connected clients
        
        Args:
            qso_data: QSO information to broadcast
        """
        if not self.clients:
            logger.debug("No WebSocket clients to broadcast to")
            return
        
        message = {
            "type": "qso_start",
            "data": qso_data
        }
        
        message_json = json.dumps(message)
        
        logger.info(f"Broadcasting QSO to {len(self.clients)} clients: {qso_data}")
        
        # Send to all clients, removing failed connections
        failed_clients = set()
        
        for client in self.clients.copy():
            try:
                await client.send(message_json)
            except ConnectionClosed:
                failed_clients.add(client)
                logger.info(f"Client {client.remote_address} disconnected during broadcast")
            except Exception as e:
                failed_clients.add(client)
                logger.error(f"Error broadcasting to client {client.remote_address}: {e}")
        
        # Remove failed clients
        self.clients -= failed_clients
        
        if failed_clients:
            logger.info(f"Removed {len(failed_clients)} failed clients, {len(self.clients)} remaining")
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status information"""
        return {
            "running": self.running,
            "port": self.config.websocket_port,
            "connected_clients": len(self.clients),
            "max_clients": self.config.max_clients
        }
