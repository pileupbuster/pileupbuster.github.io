"""
WebSocket Protocol Definition for Pileup Buster

This module defines the WebSocket message protocol for authentication and operations.
"""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Message Types
MessageType = Literal[
    # Authentication
    "auth_request", "auth_response", "auth_logout",
    
    # Admin Operations
    "admin_get_queue", "admin_complete_qso", "admin_work_next", "admin_work_specific",
    "admin_start_qso", "admin_set_frequency", "admin_clear_frequency",
    "admin_set_split", "admin_clear_split", "admin_toggle_system",
    "admin_get_status", "admin_get_current_qso",
    
    # Public Operations
    "register_callsign", "get_queue_status", "get_current_qso",
    
    # Responses
    "success", "error", "queue_update", "qso_update", "system_status_update",
    
    # System
    "ping", "pong", "welcome"
]

class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: MessageType
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None

class AuthRequest(BaseModel):
    """Authentication request message"""
    type: Literal["auth_request"] = "auth_request"
    request_id: str
    username: str
    password: str

class AuthResponse(BaseModel):
    """Authentication response message"""
    type: Literal["auth_response"] = "auth_response"
    request_id: str
    authenticated: bool
    session_token: Optional[str] = None
    message: str
    expires_at: Optional[datetime] = None

class AdminGetQueueRequest(BaseModel):
    """Request to get queue as admin"""
    type: Literal["admin_get_queue"] = "admin_get_queue"
    request_id: str
    session_token: str

class AdminCompleteQsoRequest(BaseModel):
    """Request to complete current QSO"""
    type: Literal["admin_complete_qso"] = "admin_complete_qso"
    request_id: str
    session_token: str

class AdminWorkNextRequest(BaseModel):
    """Request to work next person in queue"""
    type: Literal["admin_work_next"] = "admin_work_next"
    request_id: str
    session_token: str

class AdminStartQsoRequest(BaseModel):
    """Request to start QSO from logging software"""
    type: Literal["admin_start_qso"] = "admin_start_qso"
    request_id: str
    session_token: str
    callsign: str
    frequency_mhz: Optional[float] = None
    mode: Optional[str] = None
    source: Literal["queue", "direct"] = "direct"

class AdminSetFrequencyRequest(BaseModel):
    """Request to set frequency"""
    type: Literal["admin_set_frequency"] = "admin_set_frequency"
    request_id: str
    session_token: str
    frequency: str

class AdminClearFrequencyRequest(BaseModel):
    """Request to clear frequency"""
    type: Literal["admin_clear_frequency"] = "admin_clear_frequency"
    request_id: str
    session_token: str

class AdminToggleSystemRequest(BaseModel):
    """Request to toggle system status"""
    type: Literal["admin_toggle_system"] = "admin_toggle_system"
    request_id: str
    session_token: str
    active: bool

class RegisterCallsignRequest(BaseModel):
    """Request to register callsign (public)"""
    type: Literal["register_callsign"] = "register_callsign"
    request_id: str
    callsign: str

class SuccessResponse(BaseModel):
    """Success response message"""
    type: Literal["success"] = "success"
    request_id: str
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Error response message"""
    type: Literal["error"] = "error"
    request_id: str
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class QueueUpdateMessage(BaseModel):
    """Queue status update broadcast"""
    type: Literal["queue_update"] = "queue_update"
    timestamp: datetime = Field(default_factory=datetime.now)
    queue: list
    total: int
    max_size: int
    system_active: bool

class QsoUpdateMessage(BaseModel):
    """Current QSO update broadcast"""
    type: Literal["qso_update"] = "qso_update"
    timestamp: datetime = Field(default_factory=datetime.now)
    current_qso: Optional[Dict[str, Any]] = None

class SystemStatusUpdateMessage(BaseModel):
    """System status update broadcast"""
    type: Literal["system_status_update"] = "system_status_update"
    timestamp: datetime = Field(default_factory=datetime.now)
    active: bool

class PingMessage(BaseModel):
    """Ping message for keepalive"""
    type: Literal["ping"] = "ping"
    timestamp: datetime = Field(default_factory=datetime.now)

class PongMessage(BaseModel):
    """Pong response message"""
    type: Literal["pong"] = "pong"
    timestamp: datetime = Field(default_factory=datetime.now)

class WelcomeMessage(BaseModel):
    """Welcome message sent on connection"""
    type: Literal["welcome"] = "welcome"
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str
    server_version: str = "1.0.0"

# Error codes
class ErrorCodes:
    AUTHENTICATION_REQUIRED = "AUTH_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_MESSAGE_FORMAT = "INVALID_FORMAT"
    INVALID_REQUEST = "INVALID_REQUEST"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CALLSIGN_INVALID = "CALLSIGN_INVALID"
    QUEUE_FULL = "QUEUE_FULL"
    SYSTEM_INACTIVE = "SYSTEM_INACTIVE"
