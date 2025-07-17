"""
Server-Sent Events (SSE) and WebSocket service for real-time notifications
"""
import json
import asyncio
import logging
from typing import Dict, Set, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events that can be broadcast"""
    CURRENT_QSO = "current_qso"
    QUEUE_UPDATE = "queue_update"
    SYSTEM_STATUS = "system_status"
    FREQUENCY_UPDATE = "frequency_update"
    SPLIT_UPDATE = "split_update"


class EventBroadcaster:
    """Manages Server-Sent Event and WebSocket connections and broadcasts"""
    
    def __init__(self):
        self._sse_connections: Set[asyncio.Queue] = set()
        self._websocket_connections: Set = set()  # Will store WebSocket objects
        self._lock = asyncio.Lock()
    
    async def add_sse_connection(self, queue: asyncio.Queue):
        """Add a new SSE connection"""
        async with self._lock:
            self._sse_connections.add(queue)
            logger.info(f"Added SSE connection. Total SSE connections: {len(self._sse_connections)}")
    
    async def remove_sse_connection(self, queue: asyncio.Queue):
        """Remove an SSE connection"""
        async with self._lock:
            self._sse_connections.discard(queue)
            logger.info(f"Removed SSE connection. Total SSE connections: {len(self._sse_connections)}")
    
    async def add_websocket_connection(self, websocket):
        """Add a new WebSocket connection for event broadcasting"""
        async with self._lock:
            self._websocket_connections.add(websocket)
            logger.info(f"Added WebSocket connection for events. Total WebSocket connections: {len(self._websocket_connections)}")
    
    async def remove_websocket_connection(self, websocket):
        """Remove a WebSocket connection"""
        async with self._lock:
            self._websocket_connections.discard(websocket)
            logger.info(f"Removed WebSocket connection. Total WebSocket connections: {len(self._websocket_connections)}")
    
    # Legacy method for backward compatibility
    async def add_connection(self, queue: asyncio.Queue):
        """Add a new SSE connection (legacy method)"""
        await self.add_sse_connection(queue)
    
    # Legacy method for backward compatibility  
    async def remove_connection(self, queue: asyncio.Queue):
        """Remove an SSE connection (legacy method)"""
        await self.remove_sse_connection(queue)
    
    async def broadcast_event(self, event_type: EventType, data: Any):
        """Broadcast an event to all connected clients (both SSE and WebSocket)"""
        total_connections = len(self._sse_connections) + len(self._websocket_connections)
        
        if total_connections == 0:
            logger.debug(f"No connections to broadcast {event_type} event")
            return
        
        event_data = {
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Broadcast to SSE connections
        await self._broadcast_to_sse(event_type, event_data)
        
        # Broadcast to WebSocket connections
        await self._broadcast_to_websockets(event_type, event_data)
        
        logger.info(f"Broadcasted {event_type} event to {total_connections} total connections "
                   f"({len(self._sse_connections)} SSE, {len(self._websocket_connections)} WebSocket)")
    
    async def _broadcast_to_sse(self, event_type: EventType, event_data: Dict[str, Any]):
        """Broadcast event to SSE connections"""
        if not self._sse_connections:
            return
            
        # Format as SSE message
        sse_message = f"event: {event_type.value}\ndata: {json.dumps(event_data)}\n\n"
        
        # Send to all SSE connections
        async with self._lock:
            disconnected = set()
            for connection_queue in self._sse_connections:
                try:
                    await connection_queue.put(sse_message)
                except Exception as e:
                    logger.warning(f"Failed to send SSE event to connection: {e}")
                    disconnected.add(connection_queue)
            
            # Clean up disconnected SSE connections
            for queue in disconnected:
                self._sse_connections.discard(queue)
    
    async def _broadcast_to_websockets(self, event_type: EventType, event_data: Dict[str, Any]):
        """Broadcast event to WebSocket connections"""
        if not self._websocket_connections:
            return
        
        # Create WebSocket event message
        websocket_message = {
            "type": "event",
            "event": event_type.value,
            "data": event_data["data"],
            "timestamp": event_data["timestamp"]
        }
        
        # Send to all WebSocket connections
        async with self._lock:
            disconnected = set()
            for websocket in self._websocket_connections:
                try:
                    await websocket.send_text(json.dumps(websocket_message))
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket event to connection: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected WebSocket connections
            for websocket in disconnected:
                self._websocket_connections.discard(websocket)
    
    async def broadcast_current_qso(self, current_qso: Optional[Dict[str, Any]]):
        """Broadcast current QSO change event"""
        await self.broadcast_event(EventType.CURRENT_QSO, current_qso)
    
    async def broadcast_queue_update(self, queue_data: Dict[str, Any]):
        """Broadcast queue update event"""
        await self.broadcast_event(EventType.QUEUE_UPDATE, queue_data)
    
    async def broadcast_system_status(self, status: Dict[str, Any]):
        """Broadcast system status change event"""
        await self.broadcast_event(EventType.SYSTEM_STATUS, status)
    
    async def broadcast_frequency_update(self, frequency_data: Dict[str, Any]):
        """Broadcast frequency update event"""
        await self.broadcast_event(EventType.FREQUENCY_UPDATE, frequency_data)
    
    async def broadcast_split_update(self, split_data: Dict[str, Any]):
        """Broadcast split update event"""
        await self.broadcast_event(EventType.SPLIT_UPDATE, split_data)


# Global event broadcaster instance
event_broadcaster = EventBroadcaster()