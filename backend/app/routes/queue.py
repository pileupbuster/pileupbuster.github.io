from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any
from app.services.qrz import qrz_service
from app.database import queue_db
import logging

logger = logging.getLogger(__name__)

queue_router = APIRouter()

class CallsignRequest(BaseModel):
    callsign: str

class QueueEntry(BaseModel):
    callsign: str
    timestamp: str
    position: int

@queue_router.post('/register')
def register_callsign(request: CallsignRequest):
    """Register a callsign in the queue"""
    callsign = request.callsign.upper().strip()
    
    if not callsign:
        raise HTTPException(status_code=400, detail='Callsign is required')
    
    # Check database connection
    if not queue_db.is_connected():
        logger.error("Database not connected")
        raise HTTPException(status_code=503, detail='Database service unavailable')
    
    try:
        entry = queue_db.add_to_queue(callsign)
        return {'message': 'Callsign registered successfully', 'entry': entry}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to register callsign: {e}")
        raise HTTPException(status_code=500, detail='Failed to register callsign')

@queue_router.get('/status/{callsign}')
def get_status(callsign: str):
    """Get position of callsign in queue with QRZ.com profile information"""
    callsign = callsign.upper().strip()
    
    # Check database connection
    if not queue_db.is_connected():
        logger.error("Database not connected")
        raise HTTPException(status_code=503, detail='Database service unavailable')
    
    try:
        entry = queue_db.get_queue_position(callsign)
        if not entry:
            raise HTTPException(status_code=404, detail='Callsign not found in queue')
        
        # Add QRZ.com information
        qrz_info = qrz_service.lookup_callsign(callsign)
        entry['qrz'] = qrz_info
        
        return entry
    except Exception as e:
        logger.error(f"Failed to get callsign status: {e}")
        raise HTTPException(status_code=500, detail='Failed to get callsign status')

@queue_router.get('/list')
def list_queue():
    """Get current queue status"""
    # Check database connection
    if not queue_db.is_connected():
        logger.error("Database not connected")
        raise HTTPException(status_code=503, detail='Database service unavailable')
    
    try:
        queue = queue_db.get_full_queue()
        return {'queue': queue, 'total': len(queue)}
    except Exception as e:
        logger.error(f"Failed to get queue list: {e}")
        raise HTTPException(status_code=500, detail='Failed to get queue list')