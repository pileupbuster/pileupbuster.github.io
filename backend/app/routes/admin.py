from fastapi import APIRouter, HTTPException
from app.routes.queue import queue_storage

admin_router = APIRouter()

@admin_router.get('/queue')
def admin_queue():
    """Admin view of the queue"""
    # Update positions
    for i, entry in enumerate(queue_storage):
        entry['position'] = i + 1
    
    return {
        'queue': queue_storage,
        'total': len(queue_storage),
        'admin': True
    }

@admin_router.delete('/queue/{callsign}')
def remove_callsign(callsign: str):
    """Remove a callsign from the queue"""
    callsign = callsign.upper().strip()
    
    for i, entry in enumerate(queue_storage):
        if entry['callsign'] == callsign:
            removed_entry = queue_storage.pop(i)
            return {
                'message': f'Callsign {callsign} removed from queue',
                'removed': removed_entry
            }
    
    raise HTTPException(status_code=404, detail='Callsign not found in queue')

@admin_router.post('/queue/clear')
def clear_queue():
    """Clear the entire queue"""
    count = len(queue_storage)
    queue_storage.clear()
    
    return {
        'message': f'Queue cleared. Removed {count} entries.',
        'cleared_count': count
    }

@admin_router.post('/queue/next')
def next_callsign():
    """Process the next callsign in queue"""
    if not queue_storage:
        raise HTTPException(status_code=400, detail='Queue is empty')
    
    next_entry = queue_storage.pop(0)
    return {
        'message': f'Next callsign: {next_entry["callsign"]}',
        'processed': next_entry,
        'remaining': len(queue_storage)
    }