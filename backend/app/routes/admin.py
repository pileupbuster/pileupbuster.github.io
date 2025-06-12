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
            # If no one is in queue and no current QSO: do nothing
            # If no one is in queue but had current QSO: it was already cleared
            if current_qso:
                return {
                    'message': 'Queue is empty. Cleared current QSO.',
                    'cleared_qso': current_qso,
                    'remaining': 0
                }
            else:
                return {
                    'message': 'Queue is empty. No action taken.',
                    'remaining': 0
                }
        
        # Put the next callsign into QSO status
        new_qso = queue_db.set_current_qso(next_entry["callsign"])
        
        remaining_count = queue_db.get_queue_count()
        
        response = {
            'message': f'Next callsign: {next_entry["callsign"]} is now in QSO',
            'processed': next_entry,
            'current_qso': new_qso,
            'remaining': remaining_count
        }
        
        if current_qso:
            response['cleared_qso'] = current_qso
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.get('/status')
def get_system_status(username: str = Depends(verify_admin_credentials)):
    """Get the current system status (active/inactive)"""
    try:
        status = queue_db.get_system_status()
        return status
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
        message = f'System {action} successfully'
        
        if not request.active and status.get('queue_cleared'):
            cleared_count = status.get("cleared_count", 0)
            message += f'. Queue cleared ({cleared_count} entries removed)'
        
        return {
            'message': message,
            'status': status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f'Database error: {str(e)}'
        )