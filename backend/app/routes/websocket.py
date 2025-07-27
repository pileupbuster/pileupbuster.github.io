"""
WebSocket Routes for Pileup Buster

This module defines WebSocket endpoints for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from ..websocket_handlers import manager, handler

logger = logging.getLogger(__name__)

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for Pileup Buster
    
    Supports:
    - Authentication
    - Admin operations (queue management, QSO operations)
    - Public operations (callsign registration, status queries)
    - Real-time updates
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            
            # Handle the message
            await handler.handle_message(websocket, message)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)
