from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.database import queue_db
from app.auth import verify_admin_credentials
from app.services.events import event_broadcaster
from app.services.logger_integration import logger_service
import asyncio
import logging
import os
from datetime import datetime

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

class LoggingSoftwareQSORequest(BaseModel):
    """Request format matching your logging software's WebSocket message"""
    type: str
    data: dict

@admin_router.get('/queue')
def admin_queue(username: str = Depends(verify_admin_credentials)):
    """Admin view of the queue"""
    try:
        queue_list = queue_db.get_queue_list_with_time()
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
        
        # Send to logger integration if enabled (but prevent feedback loops)
        try:
            logger_settings = queue_db.get_logger_integration()
            if logger_settings.get('enabled', False):
                # Check if the QSO we just cleared came from the logging software
                # If so, don't send notification back to prevent feedback loop
                should_notify_logger = True
                if current_qso and current_qso.get('metadata', {}).get('started_via') == 'logging_software':
                    logger.info(f"🔄 FEEDBACK PREVENTION: Not sending {next_entry['callsign']} back to logger (previous QSO {current_qso['callsign']} came from logging software)")
                    should_notify_logger = False
                
                if should_notify_logger:
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
                    logger.info(f"📤 LOGGER: Sent QSO start notification for {next_entry['callsign']}")
        except Exception as e:
            logger.warning(f"Failed to send logger integration notification: {e}")
        
        # Broadcast the new current QSO
        try:
            await event_broadcaster.broadcast_current_qso(new_qso)
            
            # Broadcast updated queue (since someone was removed)
            queue_list = queue_db.get_queue_list_with_time()
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

@admin_router.post('/queue/work/{callsign}')
async def work_specific_callsign(callsign: str, username: str = Depends(verify_admin_credentials)):
    """Work a specific callsign from the queue (removes from queue and sets as current QSO)"""
    callsign = callsign.upper().strip()
    
    try:
        # First, check if callsign is already the current QSO
        current_qso = queue_db.get_current_qso()
        if current_qso and current_qso.get('callsign', '').upper() == callsign:
            # Already working this callsign, return success
            return {
                'message': f'Already working {callsign} (current QSO)',
                'current_qso': current_qso,
                'was_already_current': True
            }
        
        # Find the callsign in the queue
        queue_list = queue_db.get_queue_list_with_time()
        target_entry = None
        
        for entry in queue_list:
            if entry.get('callsign', '').upper() == callsign:
                target_entry = entry
                break
                
        if not target_entry:
            raise HTTPException(status_code=404, detail=f'Callsign {callsign} not found in queue or current QSO')
        
        # Clear any existing current QSO
        current_qso = queue_db.clear_current_qso()
        
        # Remove the specific callsign from queue
        removed_entry = queue_db.remove_callsign(callsign)
        
        if not removed_entry:
            raise HTTPException(status_code=404, detail=f'Callsign {callsign} could not be removed from queue')
        
        # Set as current QSO with stored QRZ information
        qrz_info = target_entry.get('qrz', {
            'callsign': callsign,
            'name': None,
            'address': None,
            'image': None,
            'error': 'QRZ information not available'
        })
        
        # Create QSO with metadata indicating it was worked from queue
        new_qso = queue_db.set_current_qso_with_metadata(
            callsign=callsign,
            qrz_info=qrz_info,
            metadata={
                'source': 'queue_specific',
                'bridge_initiated': False,
                'original_position': target_entry.get('position', 'unknown'),
                'worked_by': username
            }
        )
        
        # Send to logger integration if enabled (but prevent feedback loops)
        try:
            logger_settings = queue_db.get_logger_integration()
            if logger_settings.get('enabled', False):
                # Check if the QSO we just cleared came from the logging software
                # If so, don't send notification back to prevent feedback loop
                should_notify_logger = True
                if current_qso and current_qso.get('metadata', {}).get('started_via') == 'logging_software':
                    logger.info(f"🔄 FEEDBACK PREVENTION: Not sending {callsign} back to logger (previous QSO {current_qso['callsign']} came from logging software)")
                    should_notify_logger = False
                
                if should_notify_logger:
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
                    from app.services.logger_integration import logger_service
                    logger_service.send_qso_started(callsign, frequency_hz)
                    logger.info(f"📤 LOGGER: Sent QSO start notification for {callsign}")
        except Exception as e:
            logger.warning(f"Failed to send logger integration notification: {e}")
        
        # Broadcast the new current QSO
        try:
            await event_broadcaster.broadcast_current_qso(new_qso)
            
            # Broadcast updated queue (since someone was removed)
            queue_list = queue_db.get_queue_list_with_time()
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            await event_broadcaster.broadcast_queue_update({
                'queue': queue_list, 
                'total': len(queue_list), 
                'max_size': max_queue_size,
                'system_active': True
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast SSE events: {e}")
        
        return {
            'message': f'Now working {callsign} (taken from queue)',
            'current_qso': new_qso,
            'removed_from_queue': removed_entry,
            'was_already_current': False
        }
        
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

@admin_router.post('/qso/cancel')
async def cancel_current_qso(username: str = Depends(verify_admin_credentials)):
    """Cancel the current QSO without advancing to the next station"""
    try:
        # Clear the current QSO
        cleared_qso = queue_db.clear_current_qso()
        
        if not cleared_qso:
            return {
                'message': 'No active QSO to cancel',
                'cancelled_qso': None
            }
        
        # Broadcast that current QSO is now None
        try:
            await event_broadcaster.broadcast_current_qso(None)
        except Exception as e:
            logger.warning(f"Failed to broadcast current QSO cancel event: {e}")
        
        return {
            'message': f'QSO with {cleared_qso["callsign"]} cancelled successfully',
            'cancelled_qso': cleared_qso
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

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
            'message': f'Send to Logger {action} successfully',
            'enabled': settings['enabled'],
            'last_updated': settings['last_updated'],
            'updated_by': settings['updated_by']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')

@admin_router.post('/qso/logging-direct')
async def receive_logging_qso(request: LoggingSoftwareQSORequest):
    """
    Receive QSO data directly from logging software via HTTP POST
    No authentication required - this replaces the WebSocket bridge
    Expected format: {"type": "qso_start", "data": {...}}
    """
    try:
        # Enhanced debugging logging
        logger.info("📡 QSO LOGGING REQUEST RECEIVED:")
        logger.info(f"📋 Full Request: {request}")
        logger.info(f"📋 Request Type: {request.type}")
        logger.info(f"📋 Request Data: {request.data}")
        
        # Check if system is active
        system_status = queue_db.get_system_status()
        if not system_status.get('active', False):
            logger.warning("❌ QSO REJECTED: System is currently inactive")
            raise HTTPException(
                status_code=503, 
                detail='System is currently inactive. QSO logging is not available.'
            )
        
        # Check if logger integration is enabled
        logger_settings = queue_db.get_logger_integration()
        if not logger_settings.get('enabled', False):
            logger.warning("❌ QSO REJECTED: Send to Logger is disabled")
            raise HTTPException(
                status_code=503, 
                detail='Send to Logger is currently disabled. QSO logging is not available.'
            )
        
        logger.info("✅ SYSTEM CHECKS PASSED: System active and Send to Logger enabled")
        
        # Validate the message type
        if request.type != "qso_start":
            raise HTTPException(status_code=400, detail=f"Unsupported message type: {request.type}")
        
        # Extract QSO data
        qso_data = request.data
        callsign = qso_data.get('callsign')
        frequency_mhz = qso_data.get('frequency_mhz')
        mode = qso_data.get('mode')
        source = qso_data.get('source', 'pblog_native')
        triggered_by = qso_data.get('triggered_by')
        
        # Enhanced field extraction logging
        logger.info("🔍 EXTRACTED FIELDS:")
        logger.info(f"   📻 Callsign: '{callsign}' (type: {type(callsign)})")
        logger.info(f"   📻 Frequency: {frequency_mhz} MHz (type: {type(frequency_mhz)})")
        logger.info(f"   📻 Mode: '{mode}' (type: {type(mode)})")
        logger.info(f"   📻 Source: '{source}' (type: {type(source)})")
        logger.info(f"   📻 Triggered by: '{triggered_by}' (type: {type(triggered_by)})")
        
        if not callsign:
            raise HTTPException(status_code=400, detail="Callsign is required")
        
        logger.info(f"📻 LOGGING SOFTWARE: QSO start received for {callsign}")
        logger.info(f"   Frequency: {frequency_mhz} MHz")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Source: {source}")
        logger.info(f"   Triggered by: {triggered_by}")
        
        # 1. Clear any existing current QSO
        cleared_qso = queue_db.clear_current_qso()
        if cleared_qso:
            logger.info(f"📻 LOGGING: Cleared existing QSO with {cleared_qso['callsign']}")
        
        # 2. Check if callsign is in queue
        queue_entry = None
        qso_source = "direct"
        
        try:
            queue_list = queue_db.get_queue_list_with_time()
            for entry in queue_list:
                if entry.get('callsign', '').upper() == callsign.upper():
                    queue_entry = entry
                    qso_source = "queue"
                    break
            
            # Remove from queue if found
            if queue_entry:
                queue_db.remove_callsign(callsign)
                logger.info(f"📻 LOGGING: Removed {callsign} from queue")
            else:
                logger.info(f"📻 LOGGING: {callsign} not in queue - direct QSO")
                
        except Exception as e:
            logger.warning(f"Error checking queue for {callsign}: {e}")
        
        # 3. Get QRZ information
        qrz_info = None
        if queue_entry and queue_entry.get('qrz'):
            qrz_info = queue_entry['qrz']
        else:
            try:
                from app.services.qrz import qrz_service
                qrz_info = qrz_service.lookup_callsign(callsign)
            except Exception as e:
                logger.warning(f"QRZ lookup failed for {callsign}: {e}")
                qrz_info = {
                    'callsign': callsign,
                    'name': None,
                    'address': None,
                    'dxcc_name': None,
                    'image': None,
                    'error': 'QRZ lookup failed'
                }
        
        # 4. Create QSO with metadata
        enhanced_qso = queue_db.set_current_qso_with_metadata(
            callsign=callsign,
            qrz_info=qrz_info,
            metadata={
                'source': qso_source,
                'logging_initiated': True,
                'frequency_mhz': frequency_mhz,
                'mode': mode,
                'started_via': 'logging_software',
                'triggered_by': triggered_by,
                'logging_source': source
            }
        )
        
        # 5. Broadcast events
        try:
            await event_broadcaster.broadcast_current_qso(enhanced_qso)
            logger.info(f"📻 LOGGING: Broadcasted current QSO for {callsign}")
            
            if queue_entry:
                queue_list = queue_db.get_queue_list_with_time()
                max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                await event_broadcaster.broadcast_queue_update({
                    'queue': queue_list,
                    'total': len(queue_list),
                    'max_size': max_queue_size,
                    'system_active': True
                })
                logger.info(f"📻 LOGGING: Broadcasted queue update")
                
        except Exception as e:
            logger.warning(f"Failed to broadcast logging QSO events: {e}")
        
        # 6. Return acknowledgment in expected format
        return {
            'type': 'ack',
            'timestamp': enhanced_qso.get('metadata', {}).get('timestamp', 'unknown'),
            'received': {
                'data': qso_data,
                'type': request.type
            },
            'qso_started': {
                'callsign': callsign,
                'source': qso_source,
                'was_in_queue': queue_entry is not None,
                'frequency_mhz': frequency_mhz,
                'mode': mode
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process logging QSO: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Failed to process QSO: {str(e)}')

@admin_router.post('/qso/debug-echo')
async def debug_echo_qso(request: dict):
    """
    Debug endpoint that simply echoes back the raw request data
    Useful for testing what your logging software is actually sending
    """
    logger.info("🐛 DEBUG ECHO ENDPOINT CALLED:")
    logger.info(f"📋 Raw Request Type: {type(request)}")
    logger.info(f"📋 Raw Request Content: {request}")
    
    # Try to parse as JSON if it's a string
    if isinstance(request, str):
        try:
            import json
            parsed = json.loads(request)
            logger.info(f"📋 Parsed JSON: {parsed}")
        except:
            logger.info("📋 Could not parse as JSON")
    
    return {
        'debug_echo': True,
        'received_type': str(type(request)),
        'received_data': request,
        'message': 'This is what your logging software sent to Pileup Buster',
        'timestamp': datetime.utcnow().isoformat()
    }

@admin_router.get('/ping')
async def admin_ping(username: str = Depends(verify_admin_credentials)):
    """
    Simple authenticated ping endpoint for connection testing
    Requires admin authentication and returns pong with server info
    """
    return {
        'message': 'pong',
        'authenticated': True,
        'username': username,
        'server_time': datetime.utcnow().isoformat(),
        'ping_type': 'admin_authenticated_http',
        'status': 'healthy'
    }