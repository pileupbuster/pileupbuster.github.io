"""
WebSocket Operation Handlers

This module implements handlers for all WebSocket operations, mapping them
to the existing HTTP API functionality while maintaining consistency.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket
from datetime import datetime

# Import existing services and database access
from app.database import queue_db
from app.validation import validate_callsign
from app.services.qrz import qrz_service
from app.services.events import event_broadcaster
import os

logger = logging.getLogger(__name__)


class WebSocketOperationHandlers:
    """Handlers for all WebSocket operations."""
    
    # ========================================
    # PUBLIC OPERATIONS (No Auth Required)
    # ========================================
    
    @staticmethod
    async def handle_public_get_status(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle public.get_status operation."""
        try:
            status = queue_db.get_system_status()
            return {
                'active': status.get('active', False)
            }
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            raise Exception(f'Database error: {str(e)}')
    
    @staticmethod
    async def handle_public_get_frequency(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle public.get_frequency operation."""
        try:
            frequency_data = queue_db.get_frequency()
            if frequency_data is None:
                return {
                    'frequency': None,
                    'last_updated': None
                }
            
            return {
                'frequency': frequency_data.get('frequency'),
                'last_updated': frequency_data.get('last_updated')
            }
        except Exception as e:
            logger.error(f"Failed to get frequency: {e}")
            raise Exception(f'Database error: {str(e)}')
    
    @staticmethod
    async def handle_public_get_split(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle public.get_split operation."""
        try:
            split_data = queue_db.get_split()
            if split_data is None:
                return {
                    'split': None,
                    'last_updated': None
                }
            
            return {
                'split': split_data.get('split'),
                'last_updated': split_data.get('last_updated')
            }
        except Exception as e:
            logger.error(f"Failed to get split: {e}")
            raise Exception(f'Database error: {str(e)}')
    
    @staticmethod
    async def handle_queue_register(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queue.register operation."""
        callsign = data.get('callsign', '').upper().strip()
        
        if not callsign:
            raise Exception('Callsign is required')
        
        if not validate_callsign(callsign):
            raise Exception('Invalid callsign format. Must follow ITU standards (e.g., KC1ABC, W1AW)')
        
        try:
            # Check if system is active before allowing registration
            system_status = queue_db.get_system_status()
            if not system_status.get('active', False):
                raise Exception('System is currently inactive. Registration is not available.')
            
            # Fetch QRZ information at registration time
            qrz_info = qrz_service.lookup_callsign(callsign)
            
            # Register callsign with QRZ information
            entry = queue_db.register_callsign(callsign, qrz_info)
            
            # Broadcast updated queue
            try:
                queue_list = queue_db.get_queue_list()
                max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                await event_broadcaster.broadcast_queue_update({
                    'queue': queue_list, 
                    'total': len(queue_list), 
                    'max_size': max_queue_size,
                    'system_active': True
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast queue update event: {e}")
            
            return {
                'message': 'Callsign registered successfully', 
                'entry': entry
            }
            
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                raise Exception('Callsign already in queue')
            elif "inactive" in str(e).lower():
                raise Exception('System is currently inactive. Registration is not available.')
            elif "full" in str(e).lower():
                raise Exception('Queue is full')
            logger.error(f"Failed to register callsign: {e}")
            raise Exception('Failed to register callsign')
    
    @staticmethod
    async def handle_queue_get_status(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queue.get_status operation."""
        callsign = data.get('callsign', '').upper().strip()
        
        if not callsign:
            raise Exception('Callsign is required')
        
        try:
            # Check if system is active
            system_status = queue_db.get_system_status()
            if not system_status.get('active', False):
                raise Exception('System is currently inactive.')
            
            entry = queue_db.find_callsign(callsign)
            if not entry:
                raise Exception('Callsign not found in queue')
            
            return entry
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception('Callsign not found in queue')
            elif "inactive" in str(e).lower():
                raise Exception('System is currently inactive.')
            logger.error(f"Failed to get callsign status: {e}")
            raise Exception('Failed to get callsign status')
    
    @staticmethod
    async def handle_queue_list(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queue.list operation."""
        try:
            # Check if system is active
            system_status = queue_db.get_system_status()
            max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
            
            if not system_status.get('active', False):
                # Return empty queue if system is inactive
                return {
                    'queue': [], 
                    'total': 0, 
                    'max_size': max_queue_size,
                    'system_active': False
                }
            
            queue = queue_db.get_queue_list()
            return {
                'queue': queue, 
                'total': len(queue), 
                'max_size': max_queue_size,
                'system_active': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue list: {e}")
            raise Exception('Failed to get queue list')
    
    # ========================================
    # ADMIN OPERATIONS (Auth Required)
    # ========================================
    
    @staticmethod
    async def handle_admin_get_queue(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.get_queue operation."""
        try:
            queue_list = queue_db.get_queue_list()
            return {
                'queue': queue_list,
                'total': len(queue_list),
                'admin': True
            }
        except Exception as e:
            logger.error(f"Failed to get admin queue: {e}")
            raise Exception(f'Database error: {str(e)}')
    
    @staticmethod
    async def handle_admin_clear_queue(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.clear_queue operation."""
        try:
            # Clear the queue
            queue_db.clear_queue()
            
            # Broadcast queue update
            try:
                max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                await event_broadcaster.broadcast_queue_update({
                    'queue': [], 
                    'total': 0, 
                    'max_size': max_queue_size,
                    'system_active': True
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast queue update event: {e}")
            
            return {'message': 'Queue cleared successfully'}
            
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            raise Exception('Failed to clear queue')
    
    @staticmethod
    async def handle_admin_remove_callsign(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.remove_callsign operation."""
        callsign = data.get('callsign', '').upper().strip()
        
        if not callsign:
            raise Exception('Callsign is required')
        
        try:
            removed_entry = queue_db.remove_callsign(callsign)
            if not removed_entry:
                raise Exception('Callsign not found in queue')
            
            # Broadcast queue update
            try:
                queue_list = queue_db.get_queue_list()
                max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                await event_broadcaster.broadcast_queue_update({
                    'queue': queue_list, 
                    'total': len(queue_list), 
                    'max_size': max_queue_size,
                    'system_active': True
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast queue update event: {e}")
            
            return {
                'message': f'Callsign {callsign} removed from queue',
                'removed': removed_entry
            }
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception('Callsign not found in queue')
            logger.error(f"Failed to remove callsign: {e}")
            raise Exception('Failed to remove callsign')
    
    @staticmethod
    async def handle_admin_next_qso(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.next_qso operation."""
        try:
            # Move to next QSO
            current_qso = queue_db.next_qso()
            
            if current_qso:
                # Broadcast current QSO update
                try:
                    await event_broadcaster.broadcast_current_qso(current_qso)
                except Exception as e:
                    logger.warning(f"Failed to broadcast current QSO event: {e}")
                
                # Broadcast queue update
                try:
                    queue_list = queue_db.get_queue_list()
                    max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
                    await event_broadcaster.broadcast_queue_update({
                        'queue': queue_list, 
                        'total': len(queue_list), 
                        'max_size': max_queue_size,
                        'system_active': True
                    })
                except Exception as e:
                    logger.warning(f"Failed to broadcast queue update event: {e}")
                
                return {
                    'message': 'Moved to next QSO',
                    'current_qso': current_qso
                }
            else:
                return {
                    'message': 'No callsigns in queue',
                    'current_qso': None
                }
                
        except Exception as e:
            logger.error(f"Failed to move to next QSO: {e}")
            raise Exception('Failed to move to next QSO')
    
    @staticmethod
    async def handle_admin_complete_qso(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.complete_qso operation."""
        try:
            # Complete current QSO
            completed_qso = queue_db.complete_qso()
            
            if completed_qso:
                # Broadcast current QSO update (should be None after completion)
                try:
                    await event_broadcaster.broadcast_current_qso(None)
                except Exception as e:
                    logger.warning(f"Failed to broadcast current QSO event: {e}")
                
                return {
                    'message': 'QSO completed successfully',
                    'completed_qso': completed_qso
                }
            else:
                return {
                    'message': 'No active QSO to complete',
                    'completed_qso': None
                }
                
        except Exception as e:
            logger.error(f"Failed to complete QSO: {e}")
            raise Exception('Failed to complete QSO')
    
    @staticmethod
    async def handle_admin_set_frequency(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.set_frequency operation."""
        frequency = data.get('frequency', '').strip()
        
        if not frequency:
            raise Exception('Frequency is required')
        
        try:
            # Set frequency
            result = queue_db.set_frequency(frequency)
            
            # Broadcast frequency update
            try:
                await event_broadcaster.broadcast_frequency_update({
                    'frequency': frequency,
                    'last_updated': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast frequency update event: {e}")
            
            return {
                'message': 'Frequency updated successfully',
                'frequency': frequency
            }
            
        except Exception as e:
            logger.error(f"Failed to set frequency: {e}")
            raise Exception('Failed to set frequency')
    
    @staticmethod
    async def handle_admin_delete_frequency(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.delete_frequency operation."""
        try:
            # Delete frequency
            queue_db.delete_frequency()
            
            # Broadcast frequency update
            try:
                await event_broadcaster.broadcast_frequency_update({
                    'frequency': None,
                    'last_updated': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast frequency update event: {e}")
            
            return {
                'message': 'Frequency deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete frequency: {e}")
            raise Exception('Failed to delete frequency')
    
    @staticmethod
    async def handle_admin_set_split(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.set_split operation."""
        split = data.get('split', '').strip()
        
        if not split:
            raise Exception('Split frequency is required')
        
        try:
            # Set split
            result = queue_db.set_split(split)
            
            # Broadcast split update
            try:
                await event_broadcaster.broadcast_split_update({
                    'split': split,
                    'last_updated': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast split update event: {e}")
            
            return {
                'message': 'Split frequency updated successfully',
                'split': split
            }
            
        except Exception as e:
            logger.error(f"Failed to set split: {e}")
            raise Exception('Failed to set split frequency')
    
    @staticmethod
    async def handle_admin_delete_split(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.delete_split operation."""
        try:
            # Delete split
            queue_db.delete_split()
            
            # Broadcast split update
            try:
                await event_broadcaster.broadcast_split_update({
                    'split': None,
                    'last_updated': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast split update event: {e}")
            
            return {
                'message': 'Split frequency deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete split: {e}")
            raise Exception('Failed to delete split frequency')
    
    @staticmethod
    async def handle_admin_set_system_status(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.set_system_status operation."""
        active = data.get('active')
        
        if active is None:
            raise Exception('Active status is required')
        
        if not isinstance(active, bool):
            raise Exception('Active status must be a boolean')
        
        try:
            # Set system status
            queue_db.set_system_status(active)
            
            # Broadcast system status update
            try:
                await event_broadcaster.broadcast_system_status({
                    'active': active,
                    'last_updated': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast system status event: {e}")
            
            return {
                'message': f'System {"activated" if active else "deactivated"} successfully',
                'active': active
            }
            
        except Exception as e:
            logger.error(f"Failed to set system status: {e}")
            raise Exception('Failed to set system status')
    
    @staticmethod
    async def handle_admin_get_system_status(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin.get_system_status operation."""
        try:
            status = queue_db.get_system_status()
            return status
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            raise Exception(f'Database error: {str(e)}')
    
    # ========================================
    # SYSTEM OPERATIONS
    # ========================================
    
    @staticmethod
    async def handle_system_ping(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system.ping operation."""
        return {
            'pong': True,
            'server_time': datetime.utcnow().isoformat(),
            'message': 'Pong from WebSocket server'
        }
    
    @staticmethod
    async def handle_system_heartbeat(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system.heartbeat operation."""
        return {
            'heartbeat': True,
            'server_time': datetime.utcnow().isoformat(),
            'uptime': 'Available in future version'  # Could implement actual uptime tracking
        }
    
    @staticmethod
    async def handle_system_info(websocket: WebSocket, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system.info operation."""
        # Import OperationType here to avoid circular import
        from app.websocket_protocol import OperationType
        
        return {
            'server': 'Pileup Buster WebSocket Server',
            'version': '1.0.0',
            'protocol_version': '1.0',
            'supported_operations': [op.value for op in OperationType],
            'features': {
                'authentication': True,
                'real_time_events': True,
                'qrz_integration': True,
                'rate_limiting': True
            }
        }


def register_operation_handlers():
    """Register all operation handlers with the message dispatcher."""
    from app.websocket_protocol import get_message_dispatcher
    
    dispatcher = get_message_dispatcher()
    
    # Register public operations
    dispatcher.register_operation_handler('public.get_status', WebSocketOperationHandlers.handle_public_get_status)
    dispatcher.register_operation_handler('public.get_frequency', WebSocketOperationHandlers.handle_public_get_frequency)
    dispatcher.register_operation_handler('public.get_split', WebSocketOperationHandlers.handle_public_get_split)
    
    # Register queue operations
    dispatcher.register_operation_handler('queue.register', WebSocketOperationHandlers.handle_queue_register)
    dispatcher.register_operation_handler('queue.get_status', WebSocketOperationHandlers.handle_queue_get_status)
    dispatcher.register_operation_handler('queue.list', WebSocketOperationHandlers.handle_queue_list)
    
    # Register admin operations
    dispatcher.register_operation_handler('admin.get_queue', WebSocketOperationHandlers.handle_admin_get_queue)
    dispatcher.register_operation_handler('admin.clear_queue', WebSocketOperationHandlers.handle_admin_clear_queue)
    dispatcher.register_operation_handler('admin.remove_callsign', WebSocketOperationHandlers.handle_admin_remove_callsign)
    dispatcher.register_operation_handler('admin.next_qso', WebSocketOperationHandlers.handle_admin_next_qso)
    dispatcher.register_operation_handler('admin.complete_qso', WebSocketOperationHandlers.handle_admin_complete_qso)
    dispatcher.register_operation_handler('admin.set_frequency', WebSocketOperationHandlers.handle_admin_set_frequency)
    dispatcher.register_operation_handler('admin.delete_frequency', WebSocketOperationHandlers.handle_admin_delete_frequency)
    dispatcher.register_operation_handler('admin.set_split', WebSocketOperationHandlers.handle_admin_set_split)
    dispatcher.register_operation_handler('admin.delete_split', WebSocketOperationHandlers.handle_admin_delete_split)
    dispatcher.register_operation_handler('admin.set_system_status', WebSocketOperationHandlers.handle_admin_set_system_status)
    dispatcher.register_operation_handler('admin.get_system_status', WebSocketOperationHandlers.handle_admin_get_system_status)
    
    # Register system operations
    dispatcher.register_operation_handler('system.ping', WebSocketOperationHandlers.handle_system_ping)
    dispatcher.register_operation_handler('system.heartbeat', WebSocketOperationHandlers.handle_system_heartbeat)
    dispatcher.register_operation_handler('system.info', WebSocketOperationHandlers.handle_system_info)
    
    logger.info("Registered WebSocket operation handlers with message dispatcher")
