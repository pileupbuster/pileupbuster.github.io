from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any
from app.services.qrz import qrz_service

queue_router = APIRouter()

# In-memory storage for demo purposes
# In production, this would use MongoDB
queue_storage: List[Dict[str, Any]] = []

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
    
    # Check if callsign already in queue
    for entry in queue_storage:
        if entry['callsign'] == callsign:
            raise HTTPException(status_code=400, detail='Callsign already in queue')
    
    # Add to queue
    entry = {
        'callsign': callsign,
        'timestamp': datetime.utcnow().isoformat(),
        'position': len(queue_storage) + 1
    }
    queue_storage.append(entry)
    
    return {'message': 'Callsign registered successfully', 'entry': entry}

@queue_router.get('/status/{callsign}')
def get_status(callsign: str):
    """Get position of callsign in queue with QRZ.com profile information"""
    callsign = callsign.upper().strip()
    
    for i, entry in enumerate(queue_storage):
        if entry['callsign'] == callsign:
            entry['position'] = i + 1
            
            # Add QRZ.com information
            qrz_info = qrz_service.lookup_callsign(callsign)
            entry['qrz'] = qrz_info
            
            return entry
    
    raise HTTPException(status_code=404, detail='Callsign not found in queue')

@queue_router.get('/list')
def list_queue():
    """Get current queue status"""
    # Update positions
    for i, entry in enumerate(queue_storage):
        entry['position'] = i + 1
    
    return {'queue': queue_storage, 'total': len(queue_storage)}