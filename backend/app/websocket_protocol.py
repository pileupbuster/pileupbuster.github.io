"""
WebSocket Message Protocol Implementation

This module provides comprehensive message handling, validation, and processing
for the WebSocket server. It implements the message protocol defined in the
WebSocket Server Implementation Plan.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import WebSocket


class MessageType(Enum):
    """Valid message types for WebSocket communication."""
    REQUEST = "request"
    RESPONSE = "response" 
    EVENT = "event"
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class OperationType(Enum):
    """Valid operation types for request messages."""
    # Public operations (no auth required)
    PUBLIC_GET_STATUS = "public.get_status"
    PUBLIC_GET_FREQUENCY = "public.get_frequency"
    PUBLIC_GET_SPLIT = "public.get_split"
    QUEUE_REGISTER = "queue.register"
    QUEUE_GET_STATUS = "queue.get_status"
    QUEUE_LIST = "queue.list"
    
    # Admin operations (auth required)
    ADMIN_GET_QUEUE = "admin.get_queue"
    ADMIN_CLEAR_QUEUE = "admin.clear_queue"
    ADMIN_REMOVE_CALLSIGN = "admin.remove_callsign"
    ADMIN_NEXT_QSO = "admin.next_qso"
    ADMIN_COMPLETE_QSO = "admin.complete_qso"
    ADMIN_SET_FREQUENCY = "admin.set_frequency"
    ADMIN_DELETE_FREQUENCY = "admin.delete_frequency"
    ADMIN_SET_SPLIT = "admin.set_split"
    ADMIN_DELETE_SPLIT = "admin.delete_split"
    ADMIN_SET_SYSTEM_STATUS = "admin.set_system_status"
    ADMIN_GET_SYSTEM_STATUS = "admin.get_system_status"
    ADMIN_LOGGING_DIRECT = "admin.logging_direct"
    
    # System operations
    SYSTEM_PING = "system.ping"
    SYSTEM_HEARTBEAT = "system.heartbeat"
    SYSTEM_INFO = "system.info"


class EventType(Enum):
    """Valid event types for broadcast messages."""
    CONNECTED = "connected"
    KEEPALIVE = "keepalive"
    CURRENT_QSO = "current_qso"
    QUEUE_UPDATE = "queue_update"
    SYSTEM_STATUS = "system_status"
    FREQUENCY_UPDATE = "frequency_update"
    SPLIT_UPDATE = "split_update"


@dataclass
class RequestMessage:
    """Request message from client to server."""
    operation: str
    data: Dict[str, Any]
    type: str = MessageType.REQUEST.value
    timestamp: str = ""
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass 
class ResponseMessage:
    """Response message from server to client."""
    operation: str
    success: bool
    type: str = MessageType.RESPONSE.value
    timestamp: str = ""
    id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class EventMessage:
    """Event broadcast message from server to clients."""
    event: str
    data: Dict[str, Any]
    type: str = MessageType.EVENT.value
    timestamp: str = ""
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ErrorMessage:
    """Error message from server to client."""
    error: str
    type: str = MessageType.ERROR.value
    timestamp: str = ""
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class PingMessage:
    """Ping message for connection health checks."""
    type: str = MessageType.PING.value
    timestamp: str = ""
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class PongMessage:
    """Pong response to ping message."""
    data: Dict[str, Any]
    type: str = MessageType.PONG.value
    timestamp: str = ""
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class AuthMessage:
    """Authentication message from client."""
    data: Dict[str, str]  # username, password
    type: str = MessageType.AUTH.value
    timestamp: str = ""
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


class MessageValidator:
    """Validates incoming WebSocket messages."""
    
    @staticmethod
    def validate_message_structure(data: Dict[str, Any]) -> List[str]:
        """
        Validate basic message structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if 'type' not in data:
            errors.append("Missing required field 'type'")
            return errors
        
        message_type = data.get('type')
        
        # Validate message type
        valid_types = [t.value for t in MessageType]
        if message_type not in valid_types:
            errors.append(f"Invalid message type '{message_type}'. Valid types: {valid_types}")
        
        # Type-specific validation
        if message_type == MessageType.REQUEST.value:
            if 'operation' not in data:
                errors.append("Request messages must include 'operation' field")
            else:
                operation = data.get('operation')
                valid_operations = [op.value for op in OperationType]
                if operation not in valid_operations:
                    errors.append(f"Invalid operation '{operation}'")
        
        elif message_type == MessageType.EVENT.value:
            if 'event' not in data:
                errors.append("Event messages must include 'event' field")
            else:
                event = data.get('event')
                valid_events = [e.value for e in EventType]
                if event not in valid_events:
                    errors.append(f"Invalid event type '{event}'")
        
        elif message_type == MessageType.AUTH.value:
            if 'data' not in data:
                errors.append("Auth messages must include 'data' field")
            else:
                auth_data = data.get('data', {})
                if not isinstance(auth_data, dict):
                    errors.append("Auth 'data' field must be an object")
                elif 'username' not in auth_data or 'password' not in auth_data:
                    errors.append("Auth data must include 'username' and 'password' fields")
        
        return errors
    
    @staticmethod
    def validate_operation_data(operation: str, data: Dict[str, Any]) -> List[str]:
        """
        Validate operation-specific data requirements.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Callsign validation for queue operations
        if operation in [OperationType.QUEUE_REGISTER.value, OperationType.QUEUE_GET_STATUS.value]:
            if 'callsign' not in data:
                errors.append(f"Operation '{operation}' requires 'callsign' field")
            else:
                callsign = data.get('callsign', '').strip().upper()
                if not callsign:
                    errors.append("Callsign cannot be empty")
                elif len(callsign) < 3 or len(callsign) > 10:
                    errors.append("Callsign must be between 3 and 10 characters")
        
        # Frequency validation
        if operation in [OperationType.ADMIN_SET_FREQUENCY.value]:
            if 'frequency' not in data:
                errors.append(f"Operation '{operation}' requires 'frequency' field")
            else:
                frequency = data.get('frequency')
                if not isinstance(frequency, str) or not frequency.strip():
                    errors.append("Frequency must be a non-empty string")
        
        # Split frequency validation
        if operation in [OperationType.ADMIN_SET_SPLIT.value]:
            if 'split' not in data:
                errors.append(f"Operation '{operation}' requires 'split' field")
            else:
                split = data.get('split')
                if not isinstance(split, str) or not split.strip():
                    errors.append("Split frequency must be a non-empty string")
        
        # Callsign validation for admin operations
        if operation in [OperationType.ADMIN_REMOVE_CALLSIGN.value]:
            if 'callsign' not in data:
                errors.append(f"Operation '{operation}' requires 'callsign' field")
        
        # System status validation
        if operation in [OperationType.ADMIN_SET_SYSTEM_STATUS.value]:
            if 'active' not in data:
                errors.append(f"Operation '{operation}' requires 'active' field")
            else:
                active = data.get('active')
                if not isinstance(active, bool):
                    errors.append("'active' field must be a boolean")
        
        return errors


class MessageParser:
    """Parses and creates WebSocket message objects."""
    
    @staticmethod
    def parse_message(raw_data: str) -> Union[RequestMessage, PingMessage, AuthMessage, ErrorMessage]:
        """
        Parse raw JSON string into appropriate message object.
        
        Returns:
            Parsed message object or ErrorMessage if parsing fails
        """
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            return ErrorMessage(
                id=None,
                error=f"Invalid JSON format: {str(e)}",
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Validate message structure
        validation_errors = MessageValidator.validate_message_structure(data)
        if validation_errors:
            return ErrorMessage(
                id=data.get('id'),
                error=f"Message validation failed: {'; '.join(validation_errors)}",
                timestamp=datetime.utcnow().isoformat()
            )
        
        message_type = data.get('type')
        message_id = data.get('id')
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        
        try:
            if message_type == MessageType.REQUEST.value:
                operation = data.get('operation')
                request_data = data.get('data', {})
                
                # Validate operation-specific data
                data_errors = MessageValidator.validate_operation_data(operation, request_data)
                if data_errors:
                    return ErrorMessage(
                        id=message_id,
                        error=f"Invalid request data: {'; '.join(data_errors)}",
                        timestamp=datetime.utcnow().isoformat()
                    )
                
                return RequestMessage(
                    id=message_id,
                    operation=operation,
                    data=request_data,
                    timestamp=timestamp
                )
            
            elif message_type == MessageType.PING.value:
                return PingMessage(
                    id=message_id,
                    timestamp=timestamp
                )
            
            elif message_type == MessageType.AUTH.value:
                auth_data = data.get('data', {})
                return AuthMessage(
                    id=message_id,
                    data=auth_data,
                    timestamp=timestamp
                )
            
            else:
                return ErrorMessage(
                    id=message_id,
                    error=f"Unsupported message type for parsing: {message_type}",
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except Exception as e:
            return ErrorMessage(
                id=message_id,
                error=f"Message parsing error: {str(e)}",
                timestamp=datetime.utcnow().isoformat()
            )
    
    @staticmethod
    def create_response(request_id: Optional[str], operation: str, success: bool, 
                       data: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> ResponseMessage:
        """Create a response message."""
        return ResponseMessage(
            id=request_id,
            operation=operation,
            success=success,
            data=data,
            error=error
        )
    
    @staticmethod
    def create_event(event_type: str, data: Dict[str, Any]) -> EventMessage:
        """Create an event message."""
        return EventMessage(
            event=event_type,
            data=data
        )
    
    @staticmethod
    def create_pong(request_id: Optional[str], data: Dict[str, Any]) -> PongMessage:
        """Create a pong response."""
        return PongMessage(
            id=request_id,
            data=data
        )
    
    @staticmethod
    def create_error(request_id: Optional[str], error: str) -> ErrorMessage:
        """Create an error message."""
        return ErrorMessage(
            id=request_id,
            error=error
        )


class MessageDispatcher:
    """Dispatches messages to appropriate handlers."""
    
    def __init__(self):
        self.operation_handlers = {}
        self.event_handlers = {}
    
    def register_operation_handler(self, operation: str, handler):
        """Register a handler for a specific operation."""
        self.operation_handlers[operation] = handler
    
    def register_event_handler(self, event_type: str, handler):
        """Register a handler for a specific event type."""
        self.event_handlers[event_type] = handler
    
    async def dispatch_request(self, websocket: WebSocket, message: RequestMessage) -> ResponseMessage:
        """
        Dispatch a request message to the appropriate handler.
        
        Returns:
            Response message with result or error
        """
        operation = message.operation
        
        if operation not in self.operation_handlers:
            return MessageParser.create_response(
                message.id,
                operation,
                success=False,
                error=f"No handler registered for operation: {operation}"
            )
        
        try:
            handler = self.operation_handlers[operation]
            result = await handler(websocket, message.data)
            
            return MessageParser.create_response(
                message.id,
                operation,
                success=True,
                data=result
            )
            
        except Exception as e:
            logging.error(f"Error handling operation {operation}: {e}")
            return MessageParser.create_response(
                message.id,
                operation,
                success=False,
                error=f"Internal server error: {str(e)}"
            )


# Global message dispatcher instance
message_dispatcher = MessageDispatcher()


def get_message_dispatcher() -> MessageDispatcher:
    """Get the global message dispatcher."""
    return message_dispatcher
