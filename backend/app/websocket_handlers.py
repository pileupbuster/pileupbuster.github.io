"""
WebSocket Message Handlers for Pileup Buster

This module handles WebSocket connections, authentication, and message routing.
"""

import json
import secrets
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect
from .websocket_protocol import (
    ErrorCodes, WebSocketMessage, AuthResponse, SuccessResponse, 
    ErrorResponse, QueueUpdateMessage, QsoUpdateMessage, 
    SystemStatusUpdateMessage, PongMessage, WelcomeMessage
)
from .database import queue_db
from .services.qrz import qrz_service
from .services.events import event_broadcaster
from .validation import validate_callsign

logger = logging.getLogger(__name__)

class WebSocketSession:
    """Represents an authenticated WebSocket session"""
    def __init__(self, session_token: str, username: str, expires_at: datetime):
        self.session_token = session_token
        self.username = username
        self.expires_at = expires_at
        self.created_at = datetime.now()
        
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
        
    def is_admin(self) -> bool:
        # For now, all authenticated users are admin
        # Could be extended to support different user roles
        return True

class WebSocketConnectionManager:
    """Manages WebSocket connections and sessions"""
    
    def __init__(self):
        # Active connections
        self.connections: Set[WebSocket] = set()
        
        # Authenticated sessions
        self.sessions: Dict[str, WebSocketSession] = {}
        
        # Connection to session mapping
        self.connection_sessions: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.connections.add(websocket)
        
        # Send welcome message
        welcome = WelcomeMessage(
            message="Connected to Pileup Buster WebSocket API",
            server_version="1.0.0"
        )
        await self.send_message(websocket, welcome.dict())
        logger.info(f"WebSocket connected from {websocket.client}")
        
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        self.connections.discard(websocket)
        
        # Remove session if exists
        if websocket in self.connection_sessions:
            session_token = self.connection_sessions[websocket]
            del self.connection_sessions[websocket]
            # Keep session in case they reconnect quickly
            logger.info(f"WebSocket disconnected, session {session_token} preserved")
        
        logger.info(f"WebSocket disconnected from {websocket.client}")
        
    async def authenticate(self, websocket: WebSocket, username: str, password: str) -> tuple[bool, Optional[str]]:
        """Authenticate a WebSocket connection"""
        # Get credentials from environment
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        if not admin_username or not admin_password:
            logger.error("Admin credentials not configured")
            return False, None
            
        # Verify credentials
        if username != admin_username or password != admin_password:
            logger.warning(f"Authentication failed for username: {username}")
            return False, None
            
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour sessions
        
        # Create session
        session = WebSocketSession(session_token, username, expires_at)
        self.sessions[session_token] = session
        self.connection_sessions[websocket] = session_token
        
        logger.info(f"WebSocket authenticated: {username}, session: {session_token[:8]}...")
        return True, session_token
        
    def get_session(self, websocket: WebSocket) -> Optional[WebSocketSession]:
        """Get session for a WebSocket connection"""
        session_token = self.connection_sessions.get(websocket)
        if not session_token:
            return None
            
        session = self.sessions.get(session_token)
        if not session or session.is_expired():
            # Clean up expired session
            if session_token in self.sessions:
                del self.sessions[session_token]
            if websocket in self.connection_sessions:
                del self.connection_sessions[websocket]
            return None
            
        return session
        
    def get_session_by_token(self, session_token: str) -> Optional[WebSocketSession]:
        """Get session by token"""
        session = self.sessions.get(session_token)
        if not session or session.is_expired():
            if session_token in self.sessions:
                del self.sessions[session_token]
            return None
        return session
        
    async def send_message(self, websocket: WebSocket, message: dict):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected WebSockets"""
        if not self.connections:
            return
            
        disconnected = set()
        for websocket in self.connections:
            try:
                await self.send_message(websocket, message)
            except Exception as e:
                logger.error(f"Error broadcasting to {websocket.client}: {e}")
                disconnected.add(websocket)
                
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)
            
    async def broadcast_to_authenticated(self, message: dict):
        """Broadcast message only to authenticated WebSockets"""
        if not self.connection_sessions:
            return
            
        disconnected = set()
        for websocket, session_token in self.connection_sessions.items():
            session = self.sessions.get(session_token)
            if session and not session.is_expired():
                try:
                    await self.send_message(websocket, message)
                except Exception as e:
                    logger.error(f"Error broadcasting to authenticated {websocket.client}: {e}")
                    disconnected.add(websocket)
                    
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)

# Global connection manager
manager = WebSocketConnectionManager()

class WebSocketMessageHandler:
    """Handles incoming WebSocket messages"""
    
    def __init__(self, manager: WebSocketConnectionManager):
        self.manager = manager
        
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket message"""
        logger.info(f"Received WebSocket message: {message}")
        try:
            data = json.loads(message)
            message_type = data.get("type")
            request_id = data.get("request_id")
            
            logger.info(f"Parsed message type: {message_type}, request_id: {request_id}")
            
            if not message_type:
                logger.warning("Message missing type field")
                await self.send_error(websocket, request_id, ErrorCodes.INVALID_MESSAGE_FORMAT, 
                                    "Message type is required")
                return
                
            # Route message based on type
            if message_type == "auth_request":
                logger.info("Routing to auth_request handler")
                await self.handle_auth_request(websocket, data)
            elif message_type == "ping":
                logger.info("Routing to ping handler")
                await self.handle_ping(websocket, data)
            elif message_type.startswith("admin_"):
                logger.info("Routing to admin message handler")
                await self.handle_admin_message(websocket, data)
            else:
                logger.info("Routing to public message handler")
                await self.handle_public_message(websocket, data)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await self.send_error(websocket, None, ErrorCodes.INVALID_MESSAGE_FORMAT, 
                                "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error(websocket, None, ErrorCodes.SYSTEM_ERROR, 
                                "Internal server error")
                                
    async def handle_auth_request(self, websocket: WebSocket, data: dict):
        """Handle authentication request"""
        request_id = data.get("request_id")
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                "Username and password are required")
            return
            
        success, session_token = await self.manager.authenticate(websocket, username, password)
        
        if success:
            response = AuthResponse(
                request_id=request_id,
                authenticated=True,
                session_token=session_token,
                message="Authentication successful",
                expires_at=datetime.now() + timedelta(hours=24)
            )
        else:
            response = AuthResponse(
                request_id=request_id,
                authenticated=False,
                message="Invalid credentials"
            )
            
        await self.manager.send_message(websocket, response.dict())
        
    async def handle_ping(self, websocket: WebSocket, data: dict):
        """Handle ping message"""
        pong = PongMessage()
        await self.manager.send_message(websocket, pong.dict())
        
    async def handle_admin_message(self, websocket: WebSocket, data: dict):
        """Handle admin-only messages"""
        request_id = data.get("request_id")
        session_token = data.get("session_token")
        message_type = data.get("type")
        
        if not session_token:
            await self.send_error(websocket, request_id, ErrorCodes.AUTHENTICATION_REQUIRED,
                                "Session token is required for admin operations")
            return
            
        session = self.manager.get_session_by_token(session_token)
        if not session:
            await self.send_error(websocket, request_id, ErrorCodes.SESSION_EXPIRED,
                                "Session expired or invalid")
            return
            
        if not session.is_admin():
            await self.send_error(websocket, request_id, ErrorCodes.PERMISSION_DENIED,
                                "Admin permissions required")
            return
            
        # Route admin message
        if message_type == "admin_get_queue":
            await self.handle_admin_get_queue(websocket, data)
        elif message_type == "admin_complete_qso":
            await self.handle_admin_complete_qso(websocket, data)
        elif message_type == "admin_cancel_qso":
            await self.handle_admin_cancel_qso(websocket, data)
        elif message_type == "admin_work_next":
            await self.handle_admin_work_next(websocket, data)
        elif message_type == "admin_work_specific":
            await self.handle_admin_work_specific(websocket, data)
        elif message_type == "admin_start_qso":
            await self.handle_admin_start_qso(websocket, data)
        elif message_type == "admin_set_frequency":
            await self.handle_admin_set_frequency(websocket, data)
        elif message_type == "admin_clear_frequency":
            await self.handle_admin_clear_frequency(websocket, data)
        elif message_type == "admin_toggle_system":
            await self.handle_admin_toggle_system(websocket, data)
        elif message_type == "admin_ping":
            await self.handle_admin_ping(websocket, data)
        else:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                f"Unknown admin message type: {message_type}")
                                
    async def handle_public_message(self, websocket: WebSocket, data: dict):
        """Handle public messages"""
        message_type = data.get("type")
        request_id = data.get("request_id")
        
        if message_type == "register_callsign":
            await self.handle_register_callsign(websocket, data)
        elif message_type == "get_queue_status":
            await self.handle_get_queue_status(websocket, data)
        elif message_type == "get_current_qso":
            await self.handle_get_current_qso(websocket, data)
        else:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                f"Unknown message type: {message_type}")
                                
    async def handle_admin_get_queue(self, websocket: WebSocket, data: dict):
        """Handle admin get queue request"""
        request_id = data.get("request_id")
        
        try:
            queue = queue_db.get_queue_list_with_time()
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            system_status = queue_db.get_system_status()
            
            response = SuccessResponse(
                request_id=request_id,
                message="Queue retrieved successfully",
                data={
                    "queue": queue,
                    "total": len(queue),
                    "max_size": max_queue_size,
                    "system_active": system_status.get('active', False)
                }
            )
            await self.manager.send_message(websocket, response.dict())
            
        except Exception as e:
            logger.error(f"Error getting queue: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to retrieve queue")
                                
    async def handle_admin_complete_qso(self, websocket: WebSocket, data: dict):
        """Handle admin complete QSO request"""
        request_id = data.get("request_id")
        
        try:
            # Get current QSO before clearing it
            current_qso = queue_db.get_current_qso()
            
            # Clear current QSO without advancing queue
            cleared_qso = queue_db.clear_current_qso()
            
            response = SuccessResponse(
                request_id=request_id,
                message="QSO completed successfully"
            )
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast QSO update
            await self.broadcast_qso_update()
            
        except Exception as e:
            logger.error(f"Error completing QSO: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to complete QSO")
                                
    async def handle_admin_cancel_qso(self, websocket: WebSocket, data: dict):
        """Handle admin cancel QSO request"""
        request_id = data.get("request_id")
        
        try:
            # Clear current QSO without advancing queue
            cleared_qso = queue_db.clear_current_qso()
            
            if not cleared_qso:
                response = SuccessResponse(
                    request_id=request_id,
                    message="No active QSO to cancel",
                    data={"cancelled_qso": None}
                )
            else:
                response = SuccessResponse(
                    request_id=request_id,
                    message=f'QSO with {cleared_qso["callsign"]} cancelled successfully',
                    data={"cancelled_qso": cleared_qso}
                )
            
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast QSO update (current QSO is now None)
            await self.broadcast_qso_update()
            
        except Exception as e:
            logger.error(f"Error cancelling QSO: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to cancel QSO")
                                
    async def handle_admin_work_next(self, websocket: WebSocket, data: dict):
        """Handle admin work next request"""
        request_id = data.get("request_id")
        
        try:
            # Get next person from queue
            next_user = queue_db.get_next_from_queue()
            if not next_user:
                await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                    "No users in queue")
                return
                
            # Set as current QSO
            qrz_data = None
            try:
                qrz_data = qrz_service.lookup_callsign(next_user['callsign'])
            except Exception as e:
                logger.warning(f"QRZ lookup failed for {next_user['callsign']}: {e}")
                qrz_data = None
                
            current_qso = {
                'callsign': next_user['callsign'],
                'timestamp': datetime.now().isoformat(),
                'qrz': qrz_data,
                'metadata': {
                    'source': 'queue',
                    'bridge_initiated': False
                }
            }
            
            queue_db.set_current_qso_with_metadata(
                next_user['callsign'], 
                qrz_data, 
                current_qso['metadata']
            )
            
            response = SuccessResponse(
                request_id=request_id,
                message=f"Now working {next_user['callsign']}",
                data={"current_qso": current_qso}
            )
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast updates
            await self.broadcast_qso_update()
            await self.broadcast_queue_update()
            
        except Exception as e:
            logger.error(f"Error working next: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to work next user")
                                
    async def handle_admin_work_specific(self, websocket: WebSocket, data: dict):
        """Handle admin work specific callsign request"""
        request_id = data.get("request_id")
        callsign = data.get("callsign")
        
        if not callsign:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                "Callsign is required")
            return
            
        try:
            callsign = callsign.upper()
            
            # First, check if callsign is already the current QSO
            current_qso = queue_db.get_current_qso()
            if current_qso and current_qso.get('callsign', '').upper() == callsign:
                # Already working this callsign, return success
                response = SuccessResponse(
                    request_id=request_id,
                    message=f"Already working {callsign} (current QSO)",
                    data={"current_qso": current_qso}
                )
                await self.manager.send_message(websocket, response.dict())
                return
            
            # Find the specific callsign in the queue
            queue = queue_db.get_queue_list()
            target_entry = None
            
            for entry in queue:
                if entry['callsign'].upper() == callsign:
                    target_entry = entry
                    break
                    
            if not target_entry:
                await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                    f"Callsign {callsign} not found in queue or current QSO")
                return
                
            # Remove the specific callsign from queue
            queue_db.remove_callsign(callsign)
            
            # Set as current QSO
            qrz_data = target_entry.get('qrz')
            if not qrz_data:
                try:
                    qrz_data = qrz_service.lookup_callsign(callsign)
                except Exception as e:
                    logger.warning(f"QRZ lookup failed for {callsign}: {e}")
                    qrz_data = None
                    
            current_qso = {
                'callsign': callsign,
                'timestamp': datetime.now().isoformat(),
                'qrz': qrz_data,
                'metadata': {
                    'source': 'queue_specific',
                    'bridge_initiated': False,
                    'original_position': target_entry.get('position', 'unknown')
                }
            }
            
            queue_db.set_current_qso_with_metadata(
                callsign, 
                qrz_data, 
                current_qso['metadata']
            )
            
            response = SuccessResponse(
                request_id=request_id,
                message=f"Now working {callsign} (taken from queue)",
                data={"current_qso": current_qso}
            )
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast updates
            await self.broadcast_qso_update()
            await self.broadcast_queue_update()
            
        except Exception as e:
            logger.error(f"Error working specific callsign: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to work specific callsign")
                                
    async def handle_admin_start_qso(self, websocket: WebSocket, data: dict):
        """Handle admin start QSO request"""
        request_id = data.get("request_id")
        callsign = data.get("callsign")
        frequency_mhz = data.get("frequency_mhz")
        mode = data.get("mode")
        source = data.get("source", "direct")
        
        if not callsign:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                "Callsign is required")
            return
            
        try:
            # Validate callsign
            if not validate_callsign(callsign.upper()):
                await self.send_error(websocket, request_id, ErrorCodes.CALLSIGN_INVALID,
                                    "Invalid callsign format")
                return
                
            # Get QRZ data
            qrz_data = None
            try:
                qrz_data = qrz_service.lookup_callsign(callsign.upper())
            except Exception as e:
                logger.warning(f"QRZ lookup failed for {callsign.upper()}: {e}")
                qrz_data = None
                
            # Create QSO
            current_qso = {
                'callsign': callsign.upper(),
                'timestamp': datetime.now().isoformat(),
                'qrz': qrz_data,
                'metadata': {
                    'source': source,
                    'bridge_initiated': False,
                    'started_via': 'logging_software'
                }
            }
            
            if frequency_mhz and source != "direct":
                current_qso['metadata']['frequency_mhz'] = frequency_mhz
            if mode:
                current_qso['metadata']['mode'] = mode
                
            queue_db.set_current_qso_with_metadata(
                callsign.upper(),
                qrz_data,
                current_qso['metadata']
            )
            
            response = SuccessResponse(
                request_id=request_id,
                message=f"Started QSO with {callsign.upper()}",
                data={"current_qso": current_qso}
            )
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast QSO update
            await self.broadcast_qso_update()
            
        except Exception as e:
            logger.error(f"Error starting QSO: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to start QSO")
    async def handle_admin_set_frequency(self, websocket: WebSocket, data: dict):
        """Handle admin set frequency request"""
        request_id = data.get("request_id")
        frequency = data.get("frequency")
        
        if not frequency:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                "Frequency is required")
            return
            
        try:
            # Set frequency in database
            queue_db.set_frequency(frequency)
            
            response = SuccessResponse(
                request_id=request_id,
                message=f"Frequency set to {frequency}"
            )
            await self.manager.send_message(websocket, response.dict())
            
        except Exception as e:
            logger.error(f"Error setting frequency: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to set frequency")
                                
    async def handle_admin_clear_frequency(self, websocket: WebSocket, data: dict):
        """Handle admin clear frequency request"""
        request_id = data.get("request_id")
        
        try:
            # Clear frequency in database
            queue_db.clear_frequency()
            
            response = SuccessResponse(
                request_id=request_id,
                message="Frequency cleared"
            )
            await self.manager.send_message(websocket, response.dict())
            
        except Exception as e:
            logger.error(f"Error clearing frequency: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to clear frequency")
                                
    async def handle_admin_toggle_system(self, websocket: WebSocket, data: dict):
        """Handle admin toggle system request"""
        request_id = data.get("request_id")
        
        try:
            # Get current status and toggle it
            current_status = queue_db.get_system_status()
            current_active = current_status.get('active', False)
            new_active = not current_active  # Toggle the current state
            
            # Set the new status
            queue_db.set_system_status(new_active)
            
            status_text = "activated" if new_active else "deactivated"
            response = SuccessResponse(
                request_id=request_id,
                message=f"System {status_text} successfully",
                data={
                    "system_active": new_active,
                    "registration_enabled": new_active,
                    "previous_state": current_active,
                    "changed_by": "logging_software",
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast system status update
            update = SystemStatusUpdateMessage(active=new_active)
            await self.manager.broadcast_to_all(update.dict())
            
            # Also broadcast to SSE clients (frontend)
            await event_broadcaster.broadcast_system_status({
                "active": new_active,  # Frontend expects 'active' not 'system_active'
                "system_active": new_active,
                "registration_enabled": new_active,
                "previous_state": current_active,
                "changed_by": "logging_software",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error toggling system: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to toggle system status")
                                
    async def handle_admin_ping(self, websocket: WebSocket, data: dict):
        """Handle admin ping request with authentication"""
        request_id = data.get("request_id")
        
        try:
            # Authentication already verified in handle_admin_message
            response = SuccessResponse(
                request_id=request_id,
                message="pong",
                data={
                    "server_time": datetime.now().isoformat(),
                    "authenticated": True,
                    "ping_type": "admin_authenticated"
                }
            )
            await self.manager.send_message(websocket, response.dict())
            
        except Exception as e:
            logger.error(f"Error handling admin ping: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to process ping request")
                                
    async def handle_get_queue_status(self, websocket: WebSocket, data: dict):
        """Handle public get queue status request"""
        request_id = data.get("request_id")
        
        try:
            system_status = queue_db.get_system_status()
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            
            if not system_status.get('active', False):
                # Return empty queue if system is inactive
                queue_data = {
                    'queue': [], 
                    'total': 0, 
                    'max_size': max_queue_size,
                    'system_active': False
                }
            else:
                queue = queue_db.get_queue_list_with_time()
                queue_data = {
                    'queue': queue, 
                    'total': len(queue), 
                    'max_size': max_queue_size,
                    'system_active': True
                }
            
            response = SuccessResponse(
                request_id=request_id,
                message="Queue status retrieved",
                data=queue_data
            )
            await self.manager.send_message(websocket, response.dict())
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to retrieve queue status")
                                
    async def handle_get_current_qso(self, websocket: WebSocket, data: dict):
        """Handle get current QSO request"""
        request_id = data.get("request_id")
        
        try:
            current_qso = queue_db.get_current_qso()
            
            response = SuccessResponse(
                request_id=request_id,
                message="Current QSO retrieved",
                data={"current_qso": current_qso}
            )
            await self.manager.send_message(websocket, response.dict())
            
        except Exception as e:
            logger.error(f"Error getting current QSO: {e}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                "Failed to retrieve current QSO")
                                
    async def handle_register_callsign(self, websocket: WebSocket, data: dict):
        """Handle public callsign registration"""
        request_id = data.get("request_id")
        callsign = data.get("callsign")
        
        if not callsign:
            await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                "Callsign is required")
            return
            
        try:
            # Check if system is active
            system_status = queue_db.get_system_status()
            if not system_status.get('active', False):
                await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_INACTIVE,
                                    "System is currently inactive")
                return
                
            # Validate callsign
            if not validate_callsign(callsign.upper()):
                await self.send_error(websocket, request_id, ErrorCodes.CALLSIGN_INVALID,
                                    "Invalid callsign format")
                return
                
            # Check queue size
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            current_queue = queue_db.get_queue_list()
            
            if len(current_queue) >= max_queue_size:
                await self.send_error(websocket, request_id, ErrorCodes.QUEUE_FULL,
                                    "Queue is currently full")
                return
                
            # Check for duplicates
            for entry in current_queue:
                if entry['callsign'].upper() == callsign.upper():
                    await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                        "Callsign already in queue")
                    return
                    
            # Get QRZ data first
            qrz_data = None
            try:
                qrz_data = qrz_service.lookup_callsign(callsign.upper())
            except Exception as e:
                logger.warning(f"QRZ lookup failed for {callsign.upper()}: {e}")
                    
            # Add to queue (using the same method as HTTP API)
            new_entry = queue_db.register_callsign(callsign.upper(), qrz_data)
            
            response = SuccessResponse(
                request_id=request_id,
                message=f"Callsign {callsign.upper()} registered successfully",
                data={"entry": new_entry}
            )
            await self.manager.send_message(websocket, response.dict())
            
            # Broadcast queue update
            await self.broadcast_queue_update()
            
        except ValueError as e:
            # Handle specific validation errors from register_callsign
            error_msg = str(e)
            if "already in queue" in error_msg.lower():
                await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                    "Callsign already in queue")
            elif "queue is full" in error_msg.lower():
                await self.send_error(websocket, request_id, ErrorCodes.QUEUE_FULL,
                                    error_msg)
            elif "system is currently inactive" in error_msg.lower():
                await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_INACTIVE,
                                    "System is currently inactive")
            else:
                await self.send_error(websocket, request_id, ErrorCodes.INVALID_REQUEST,
                                    error_msg)
        except Exception as e:
            logger.error(f"Error registering callsign: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await self.send_error(websocket, request_id, ErrorCodes.SYSTEM_ERROR,
                                f"Failed to register callsign: {str(e)}")
                                
    async def send_error(self, websocket: WebSocket, request_id: Optional[str], 
                        error_code: str, message: str):
        """Send error response"""
        error = ErrorResponse(
            request_id=request_id or "unknown",
            error_code=error_code,
            message=message
        )
        await self.manager.send_message(websocket, error.dict())
        
    async def broadcast_queue_update(self):
        """Broadcast queue update to all connections (WebSocket + SSE)"""
        try:
            queue = queue_db.get_queue_list_with_time()
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            system_status = queue_db.get_system_status()
            
            # Broadcast to WebSocket clients
            update = QueueUpdateMessage(
                queue=queue,
                total=len(queue),
                max_size=max_queue_size,
                system_active=system_status.get('active', False)
            )
            await self.manager.broadcast_to_all(update.dict())
            
            # Broadcast to SSE clients (web frontend)
            queue_data = {
                "queue": queue,
                "total": len(queue),
                "max_size": max_queue_size,
                "system_active": system_status.get('active', False)
            }
            await event_broadcaster.broadcast_queue_update(queue_data)
            
        except Exception as e:
            logger.error(f"Error broadcasting queue update: {e}")
            
    async def broadcast_qso_update(self):
        """Broadcast QSO update to all connections (WebSocket + SSE)"""
        try:
            current_qso = queue_db.get_current_qso()
            
            # Broadcast to WebSocket clients
            update = QsoUpdateMessage(
                current_qso=current_qso
            )
            await self.manager.broadcast_to_all(update.dict())
            
            # Broadcast to SSE clients (web frontend)
            await event_broadcaster.broadcast_current_qso(current_qso)
            
        except Exception as e:
            logger.error(f"Error broadcasting QSO update: {e}")

# Global message handler
handler = WebSocketMessageHandler(manager)
