from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.database import queue_db
from app.auth import verify_admin_credentials

admin_router = APIRouter()

class SystemStatusRequest(BaseModel):
    active: bool

@admin_router.get('/queue')
def admin_queue(username: str = Depends(verify_admin_credentials)):
    """Admin view of the queue"""
    try:
        queue_list = queue_db.get_queue_list()
        return {
            'queue': queue_list,
            'total': len(queue_list),
            'admin': True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.delete('/queue/{callsign}')
def remove_callsign(callsign: str, username: str = Depends(verify_admin_credentials)):
    """Remove a callsign from the queue"""
    callsign = callsign.upper().strip()
    
    try:
        removed_entry = queue_db.remove_callsign(callsign)
        if removed_entry:
            return {
                'message': f'Callsign {callsign} removed from queue',
                'removed': removed_entry
            }
        raise HTTPException(status_code=404, detail='Callsign not found in queue')
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail='Callsign not found in queue')
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/queue/clear')
def clear_queue(username: str = Depends(verify_admin_credentials)):
    """Clear the entire queue"""
    try:
        count = queue_db.clear_queue()
        return {
            'message': f'Queue cleared. Removed {count} entries.',
            'cleared_count': count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/queue/next')
def next_callsign(username: str = Depends(verify_admin_credentials)):
    """Process the next callsign in queue and manage QSO status"""
    try:
        # Clear any existing current QSO
        current_qso = queue_db.clear_current_qso()
        
        # Get the next callsign from queue
        next_entry = queue_db.get_next_callsign()
        
        if not next_entry:
            # If no one is in queue, return None for current_qso
            return None
        
        # Put the next callsign into QSO status
        new_qso = queue_db.set_current_qso(next_entry["callsign"])
        
        # Add QRZ.com information to the current QSO
        from app.services.qrz import qrz_service
        qrz_info = qrz_service.lookup_callsign(next_entry["callsign"])
        new_qso['qrz'] = qrz_info
        
        return new_qso
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/status')
def set_system_status(
    request: SystemStatusRequest, 
    username: str = Depends(verify_admin_credentials)
):
    """Set the system status (activate/deactivate)"""
    try:
        status = queue_db.set_system_status(request.active, username)
        action = "activated" if request.active else "deactivated"
        cleared_count = status.get("cleared_count", 0)
        message = f'System {action} successfully. Queue cleared ({cleared_count} entries removed)'
        
        return {
            'message': message,
            'status': status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f'Database error: {str(e)}'
        )