from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any
from app.database import queue_db

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
    
    try:
        entry = queue_db.register_callsign(callsign)
        return {'message': 'Callsign registered successfully', 'entry': entry}
    except ValueError as e:
        if "already in queue" in str(e):
            raise HTTPException(status_code=400, detail='Callsign already in queue')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@queue_router.get('/status/{callsign}')
def get_status(callsign: str):
    """Get position of callsign in queue"""
    callsign = callsign.upper().strip()
    
    try:
        entry = queue_db.find_callsign(callsign)
        if entry:
            return entry
        raise HTTPException(status_code=404, detail='Callsign not found in queue')
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail='Callsign not found in queue')
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@queue_router.get('/list')
def list_queue():
    """Get current queue status"""
    try:
        queue_list = queue_db.get_queue_list()
        return {'queue': queue_list, 'total': len(queue_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')