from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.database import queue_db
from app.auth import verify_admin_credentials
from app.services.events import event_broadcaster
from app.services.logger_integration import logger_service
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

admin_router = APIRouter()

class SystemStatusRequest(BaseModel):
    active: bool

class FrequencyRequest(BaseModel):
    frequency: str

class SplitRequest(BaseModel):
    split: str

class LoggerIntegrationRequest(BaseModel):
    enabled: bool

class BridgeQSORequest(BaseModel):
    callsign: str
    frequency: float = None
    mode: str = None
    source: str = "bridge"

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
async def next_callsign(username: str = Depends(verify_admin_credentials)):
    """Process the next callsign in queue and manage QSO status"""
    try:
        # Clear any existing current QSO
        current_qso = queue_db.clear_current_qso()
        
        # Get the next callsign from queue
        next_entry = queue_db.get_next_callsign()
        
        if not next_entry:
            # If no one is in queue, return None for current_qso
            # Broadcast that current QSO is now None
            try:
                await event_broadcaster.broadcast_current_qso(None)
            except Exception as e:
                logger.warning(f"Failed to broadcast current QSO event: {e}")
            return None
        
        # Put the next callsign into QSO status with stored QRZ information
        qrz_info = next_entry.get('qrz', {
            'callsign': next_entry["callsign"],
            'name': None,
            'address': None,
            'image': None,
            'error': 'QRZ information not available'
        })
        new_qso = queue_db.set_current_qso(next_entry["callsign"], qrz_info)
        
        # Send to logger integration if enabled
        try:
            logger_settings = queue_db.get_logger_integration()
            if logger_settings.get('enabled', False):
                # Get current frequency for UDP packet
                frequency_hz = None
                try:
                    freq_data = queue_db.get_frequency()
                    if freq_data and freq_data.get('frequency'):
                        # Convert frequency to Hz for WSJT-X protocol
                        freq_str = freq_data['frequency'].replace(' ', '').replace('KHz', '').replace('kHz', '').replace('MHz', '').replace('mHz', '')
                        try:
                            freq_float = float(freq_str)
                            # Determine if it's in kHz or MHz based on magnitude
                            if freq_float > 1000:
                                frequency_hz = int(freq_float * 1000)  # kHz to Hz
                            else:
                                frequency_hz = int(freq_float * 1_000_000)  # MHz to Hz
                        except ValueError:
                            logger.warning(f"Could not parse frequency for logger: {freq_str}")
                except Exception as e:
                    logger.warning(f"Could not get frequency for logger integration: {e}")
                
                # Send QSO start notification to logger
                logger_service.send_qso_started(next_entry["callsign"], frequency_hz)
        except Exception as e:
            logger.warning(f"Failed to send logger integration notification: {e}")
        
        # Broadcast the new current QSO
        try:
            await event_broadcaster.broadcast_current_qso(new_qso)
            
            # Broadcast updated queue (since someone was removed)
            queue_list = queue_db.get_queue_list()
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            await event_broadcaster.broadcast_queue_update({
                'queue': queue_list, 
                'total': len(queue_list), 
                'max_size': max_queue_size,
                'system_active': True
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast SSE events: {e}")
        
        return new_qso
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/qso/complete')
async def complete_current_qso(username: str = Depends(verify_admin_credentials)):
    """Complete the current QSO without advancing to the next station"""
    try:
        # Clear the current QSO
        cleared_qso = queue_db.clear_current_qso()
        
        if not cleared_qso:
            return {
                'message': 'No active QSO to complete',
                'cleared_qso': None
            }
        
        # Broadcast that current QSO is now None
        try:
            await event_broadcaster.broadcast_current_qso(None)
        except Exception as e:
            logger.warning(f"Failed to broadcast current QSO clear event: {e}")
        
        return {
            'message': f'QSO with {cleared_qso["callsign"]} completed successfully',
            'cleared_qso': cleared_qso
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/qso/bridge-start')
async def start_bridge_qso(
    request: BridgeQSORequest,
    username: str = Depends(verify_admin_credentials)
):
    """Start QSO initiated from bridge (QLog) - automatically clear current and set new"""
    try:
        # 1. Clear any existing current QSO (reuse existing routine)
        cleared_qso = queue_db.clear_current_qso()
        
        # 2. Check if callsign is in queue (for source determination)
        queue_entry = None
        qso_source = "direct"  # Default to direct
        
        try:
            # Look for the callsign in the queue
            queue_list = queue_db.get_queue_list()
            for entry in queue_list:
                if entry.get('callsign', '').upper() == request.callsign.upper():
                    queue_entry = entry
                    qso_source = "queue"
                    break
            
            # If found in queue, remove it
            if queue_entry:
                queue_db.remove_callsign(request.callsign)
                logger.info(f"Bridge QSO: Removed {request.callsign} from queue")
            else:
                logger.info(f"Bridge QSO: {request.callsign} not in queue - marked as direct")
                
        except Exception as e:
            logger.warning(f"Error checking queue for {request.callsign}: {e}")
            # Continue with direct QSO if queue check fails
        
        # 3. Get QRZ information (use existing from queue or lookup fresh)
        qrz_info = None
        if queue_entry and queue_entry.get('qrz'):
            qrz_info = queue_entry['qrz']
            logger.info(f"Bridge QSO: Using existing QRZ info for {request.callsign}")
        else:
            # Fresh QRZ lookup for direct QSOs
            try:
                from app.services.qrz import qrz_service
                qrz_info = qrz_service.lookup_callsign(request.callsign)
                logger.info(f"Bridge QSO: Fresh QRZ lookup for {request.callsign} - Result: {qrz_info}")
            except Exception as e:
                logger.warning(f"QRZ lookup failed for {request.callsign}: {e}")
                qrz_info = {
                    'callsign': request.callsign,
                    'name': None,
                    'address': None,
                    'dxcc_name': None,
                    'image': None,
                    'error': 'QRZ lookup failed'
                }
        
        # 4. Create enhanced QSO entry with bridge metadata
        enhanced_qso = queue_db.set_current_qso_with_metadata(
            callsign=request.callsign,
            qrz_info=qrz_info,
            metadata={
                'source': qso_source,  # 'queue' or 'direct'
                'bridge_initiated': True,
                'frequency_mhz': request.frequency,
                'mode': request.mode,
                'started_via': 'bridge',
                'bridge_timestamp': request.callsign  # For debugging
            }
        )
        
        # 5. Broadcast events (reuse existing SSE)
        try:
            await event_broadcaster.broadcast_current_qso(enhanced_qso)
            logger.info(f"Bridge QSO: Broadcasted current QSO for {request.callsign}")
            
            # If someone was removed from queue, broadcast queue update
            if queue_entry:
                queue_list = queue_db.get_queue_list()
                max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                await event_broadcaster.broadcast_queue_update({
                    'queue': queue_list,
                    'total': len(queue_list),
                    'max_size': max_queue_size,
                    'system_active': True
                })
                logger.info(f"Bridge QSO: Broadcasted queue update after removing {request.callsign}")
                
        except Exception as e:
            logger.warning(f"Failed to broadcast bridge QSO events: {e}")
        
        return {
            'message': f'Bridge QSO with {request.callsign} started successfully',
            'new_qso': enhanced_qso,
            'cleared_qso': cleared_qso,
            'source': qso_source,
            'was_in_queue': queue_entry is not None,
            'frequency_mhz': request.frequency,
            'mode': request.mode
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start bridge QSO for {request.callsign}: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Failed to start bridge QSO: {str(e)}')

@admin_router.post('/status')
async def set_system_status(
    request: SystemStatusRequest, 
    username: str = Depends(verify_admin_credentials)
):
    """Set the system status (activate/deactivate)"""
    try:
        status = queue_db.set_system_status(request.active, username)
        action = "activated" if request.active else "deactivated"
        cleared_count = status.get("cleared_count", 0)
        qso_cleared = status.get("qso_cleared", False)
        
        # Build message with queue and QSO clearing information
        message_parts = [f'System {action} successfully.']
        message_parts.append(f'Queue cleared ({cleared_count} entries removed)')
        if qso_cleared:
            message_parts.append('Current QSO cleared')
        message = '. '.join(message_parts)
        
        # Broadcast system status change
        try:
            await event_broadcaster.broadcast_system_status({
                'active': request.active
            })
            
            # If system was deactivated, also broadcast empty queue and no current QSO
            if not request.active:
                await event_broadcaster.broadcast_current_qso(None)
                max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                await event_broadcaster.broadcast_queue_update({
                    'queue': [], 
                    'total': 0, 
                    'max_size': max_queue_size,
                    'system_active': False
                })
                
                # Clear split when system goes offline
                try:
                    split_data = queue_db.clear_split(username)
                    await event_broadcaster.broadcast_split_update(split_data)
                except Exception as e:
                    logger.warning(f"Failed to clear split when going offline: {e}")
        except Exception as e:
            logger.warning(f"Failed to broadcast system status events: {e}")
        
        return {
            'message': message,
            'status': status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f'Database error: {str(e)}'
        )

@admin_router.get('/status')
def get_system_status(username: str = Depends(verify_admin_credentials)):
    """Get the current system status"""
    try:
        status = queue_db.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/frequency')
async def set_frequency(
    request: FrequencyRequest, 
    username: str = Depends(verify_admin_credentials)
):
    """Set the current transmission frequency (admin only)"""
    try:
        frequency_data = queue_db.set_frequency(request.frequency, username)
        
        # Broadcast frequency update
        try:
            await event_broadcaster.broadcast_frequency_update(frequency_data)
        except Exception as e:
            logger.warning(f"Failed to broadcast frequency update event: {e}")
        
        return {
            'message': f'Frequency set to {request.frequency}',
            'frequency_data': frequency_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.delete('/frequency')
async def clear_frequency(
    username: str = Depends(verify_admin_credentials)
):
    """Clear the current transmission frequency (admin only)"""
    try:
        frequency_data = queue_db.clear_frequency(username)
        
        # Broadcast frequency update (with None frequency)
        try:
            await event_broadcaster.broadcast_frequency_update({
                'frequency': None,
                'last_updated': frequency_data['last_updated'],
                'updated_by': frequency_data['updated_by']
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast frequency clear event: {e}")
        
        return {
            'message': 'Frequency cleared successfully',
            'frequency_data': frequency_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/split')
async def set_split(
    request: SplitRequest, 
    username: str = Depends(verify_admin_credentials)
):
    """Set the current split value (admin only)"""
    try:
        split_data = queue_db.set_split(request.split, username)
        
        # Broadcast split update
        try:
            await event_broadcaster.broadcast_split_update(split_data)
        except Exception as e:
            logger.warning(f"Failed to broadcast split update event: {e}")
        
        return {
            'message': f'Split set to {request.split}',
            'split_data': split_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.delete('/split')
async def clear_split(
    username: str = Depends(verify_admin_credentials)
):
    """Clear the current split value (admin only)"""
    try:
        split_data = queue_db.clear_split(username)
        
        # Broadcast split update
        try:
            await event_broadcaster.broadcast_split_update(split_data)
        except Exception as e:
            logger.warning(f"Failed to broadcast split clear event: {e}")
        
        return {
            'message': 'Split cleared',
            'split_data': split_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.get('/current')
def admin_get_current_qso(username: str = Depends(verify_admin_credentials)):
    """Admin endpoint to get current QSO regardless of system status"""
    try:
        current_qso = queue_db.get_current_qso()
        return current_qso
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.get('/logger-integration')
def get_logger_integration(username: str = Depends(verify_admin_credentials)):
    """Get the logger integration settings"""
    try:
        settings = queue_db.get_logger_integration()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/logger-integration')
async def set_logger_integration(
    request: LoggerIntegrationRequest, 
    username: str = Depends(verify_admin_credentials)
):
    """Set the logger integration status"""
    try:
        settings = queue_db.set_logger_integration(request.enabled, username)
        
        # Enable or disable the logger service based on the setting
        if request.enabled:
            logger_service.enable()
        else:
            logger_service.disable()
        
        action = "enabled" if request.enabled else "disabled"
        return {
            'message': f'Logger integration {action} successfully',
            'enabled': settings['enabled'],
            'last_updated': settings['last_updated'],
            'updated_by': settings['updated_by']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')