"""
WebSocket routes for real-time communication with desktop applications.

This module provides WebSocket endpoints that mirror the HTTP API functionality
while maintaining full backward compatibility with existing SSE and HTTP systems.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.exceptions import WebSocketException
import os

from app.auth import verify_admin_credentials_direct
from app.websocket_protocol import (
    MessageParser, MessageDispatcher, RequestMessage, 
    PingMessage, AuthMessage, ErrorMessage, ResponseMessage, PongMessage,
    MessageType, OperationType, get_message_dispatcher
)


# WebSocket connection manager
class ConnectionManager:
    """Manages active WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Store active connections with metadata
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        self.max_connections = int(os.getenv('WEBSOCKET_MAX_CONNECTIONS', '100'))
        self.heartbeat_interval = int(os.getenv('WEBSOCKET_HEARTBEAT_INTERVAL', '30'))
        
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None) -> bool:
        """Accept a new WebSocket connection."""
        try:
            # Check connection limit
            if len(self.active_connections) >= self.max_connections:
                await websocket.close(code=1013, reason="Server overloaded")
                return False
                
            await websocket.accept()
            
            # Store connection metadata
            connection_info = {
                'connected_at': datetime.utcnow().isoformat(),
                'authenticated': False,
                'user_type': 'public',
                'last_ping': datetime.utcnow(),
                'client_info': client_info or {}
            }
            
            self.active_connections[websocket] = connection_info
            
            # Register connection with event broadcaster for real-time events
            from app.services.events import event_broadcaster
            await event_broadcaster.add_websocket_connection(websocket)
            
            logging.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
            
            # Send welcome message using new protocol
            from app.websocket_protocol import MessageParser, EventType
            
            welcome_event = MessageParser.create_event(
                EventType.CONNECTED.value,
                {
                    "message": "WebSocket connection established",
                    "server_time": datetime.utcnow().isoformat(),
                    "connection_id": id(websocket),
                    "events_enabled": True  # Indicate that real-time events are enabled
                }
            )
            
            await self.send_personal_message(websocket, welcome_event)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to establish WebSocket connection: {e}")
            return False
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            connection_info = self.active_connections[websocket]
            del self.active_connections[websocket]
            
            # Unregister from event broadcaster
            from app.services.events import event_broadcaster
            import asyncio
            try:
                # Create task to handle async cleanup
                asyncio.create_task(event_broadcaster.remove_websocket_connection(websocket))
            except Exception as e:
                logging.warning(f"Failed to unregister WebSocket from event broadcaster: {e}")
            
            logging.info(
                f"WebSocket connection closed. "
                f"Was authenticated: {connection_info.get('authenticated', False)}. "
                f"Total connections: {len(self.active_connections)}"
            )
    
    async def send_personal_message(self, websocket: WebSocket, message):
        """Send a message to a specific WebSocket connection."""
        try:
            # Handle both new protocol messages and legacy dict messages
            if hasattr(message, 'to_json'):
                # New protocol message object
                await websocket.send_text(message.to_json())
            else:
                # Legacy dict message (for backwards compatibility)
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            logging.error(f"Failed to send message to WebSocket: {e}")
            # Connection might be closed, remove it
            self.disconnect(websocket)
    
    async def broadcast(self, message, auth_required: bool = False):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
            
        # Filter connections based on auth requirement
        target_connections = []
        for websocket, connection_info in self.active_connections.items():
            if not auth_required or connection_info.get('authenticated', False):
                target_connections.append(websocket)
        
        if not target_connections:
            return
            
        # Send message to all target connections
        disconnect_list = []
        for websocket in target_connections:
            try:
                # Handle both new protocol messages and legacy dict messages
                if hasattr(message, 'to_json'):
                    # New protocol message object
                    await websocket.send_text(message.to_json())
                else:
                    # Legacy dict message (for backwards compatibility)
                    await websocket.send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Failed to broadcast to WebSocket: {e}")
                disconnect_list.append(websocket)
        
        # Clean up failed connections
        for websocket in disconnect_list:
            self.disconnect(websocket)
    
    def authenticate_connection(self, websocket: WebSocket, user_type: str = 'admin'):
        """Mark a connection as authenticated."""
        if websocket in self.active_connections:
            self.active_connections[websocket]['authenticated'] = True
            self.active_connections[websocket]['user_type'] = user_type
            logging.info(f"WebSocket connection authenticated as {user_type}")
    
    def is_authenticated(self, websocket: WebSocket) -> bool:
        """Check if a connection is authenticated."""
        connection_info = self.active_connections.get(websocket, {})
        return connection_info.get('authenticated', False)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)
    
    def get_authenticated_count(self) -> int:
        """Get number of authenticated connections."""
        return sum(1 for info in self.active_connections.values() 
                  if info.get('authenticated', False))


# Global connection manager instance
manager = ConnectionManager()

# Create router
websocket_router = APIRouter()


@websocket_router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for client connections.
    
    Handles authentication, message routing, and connection management.
    """
    # Accept connection
    connected = await manager.connect(websocket)
    if not connected:
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Update last ping time
            if websocket in manager.active_connections:
                manager.active_connections[websocket]['last_ping'] = datetime.utcnow()
            
            # Route message to appropriate handler using new protocol
            await handle_websocket_message(websocket, data)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, raw_message: str):
    """
    Route incoming WebSocket messages using the new protocol system.
    
    Args:
        websocket: The WebSocket connection
        raw_message: Raw JSON message string from client
    """
    try:
        # Parse message using the new protocol system
        message = MessageParser.parse_message(raw_message)
        
        # If parsing failed, send error response
        if isinstance(message, ErrorMessage):
            await send_message_to_client(websocket, message)
            return
        
        # Handle different message types
        if isinstance(message, RequestMessage):
            await handle_request_message(websocket, message)
        elif isinstance(message, PingMessage):
            await handle_ping_message(websocket, message)
        elif isinstance(message, AuthMessage):
            await handle_auth_message(websocket, message)
        else:
            error_msg = MessageParser.create_error(
                getattr(message, 'id', None),
                f"Unsupported message type: {type(message).__name__}"
            )
            await send_message_to_client(websocket, error_msg)
            
    except Exception as e:
        logging.error(f"Error handling WebSocket message: {e}")
        error_msg = MessageParser.create_error(
            None,
            f"Internal server error: {str(e)}"
        )
        await send_message_to_client(websocket, error_msg)


async def handle_request_message(websocket: WebSocket, message: RequestMessage):
    """Handle request messages using the message dispatcher."""
    # Check if operation requires authentication
    requires_auth = message.operation.startswith('admin.')
    
    if requires_auth and not manager.is_authenticated(websocket):
        error_msg = MessageParser.create_response(
            message.id,
            message.operation,
            success=False,
            error="Authentication required for this operation"
        )
        await send_message_to_client(websocket, error_msg)
        return
    
    # Dispatch to appropriate handler
    dispatcher = get_message_dispatcher()
    response = await dispatcher.dispatch_request(websocket, message)
    await send_message_to_client(websocket, response)


async def handle_ping_message(websocket: WebSocket, message: PingMessage):
    """Handle ping/pong for connection health using new protocol."""
    pong_msg = MessageParser.create_pong(
        message.id,
        {
            "server_time": datetime.utcnow().isoformat(),
            "connection_count": manager.get_connection_count(),
            "authenticated_count": manager.get_authenticated_count()
        }
    )
    await send_message_to_client(websocket, pong_msg)


async def handle_auth_message(websocket: WebSocket, message: AuthMessage):
    """Handle authentication requests using new protocol."""
    try:
        username = message.data.get('username')
        password = message.data.get('password')
        
        if not username or not password:
            response = MessageParser.create_response(
                message.id,
                "auth",
                success=False,
                error="Username and password required"
            )
        elif verify_admin_credentials_direct(username, password):
            manager.authenticate_connection(websocket, 'admin')
            response = MessageParser.create_response(
                message.id,
                "auth",
                success=True,
                data={
                    "authenticated": True,
                    "user_type": "admin",
                    "message": "Authentication successful"
                }
            )
        else:
            response = MessageParser.create_response(
                message.id,
                "auth",
                success=False,
                error="Invalid credentials"
            )
        
        await send_message_to_client(websocket, response)
        
    except Exception as e:
        error_msg = MessageParser.create_response(
            message.id,
            "auth",
            success=False,
            error=f"Authentication error: {str(e)}"
        )
        await send_message_to_client(websocket, error_msg)


async def send_message_to_client(websocket: WebSocket, message):
    """Send a WebSocket message to a client using the new protocol."""
    try:
        await websocket.send_text(message.to_json())
    except Exception as e:
        logging.error(f"Failed to send message to WebSocket: {e}")
        # Connection might be closed, remove it
        manager.disconnect(websocket)


# Function to get the connection manager (for use by other modules)
def get_connection_manager() -> ConnectionManager:
    """Get the global WebSocket connection manager."""
    return manager
