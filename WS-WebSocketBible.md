# WebSocket Integration Bible - Pileup Buster

**Quick Reference Guide for External Software Integration**

## Connection Details

**Endpoint**: `ws://localhost:8000/api/ws`  
**Protocol**: JSON messages over WebSocket  
**Authentication**: Session-based tokens (24-hour expiry)

---

## Authentication Flow

### 1. Connect & Authenticate

**Send**:
```json
{
  "type": "auth_request",
  "request_id": "auth_001",
  "username": "admin",
  "password": "your_password"
}
```

**Receive (Success)**:
```json
{
  "type": "auth_response",
  "request_id": "auth_001",
  "success": true,
  "session_token": "abc123...",
  "expires_at": "2025-07-24T12:00:00Z"
}
```

**Receive (Failure)**:
```json
{
  "type": "error",
  "request_id": "auth_001",
  "error_code": "AUTHENTICATION_FAILED",
  "message": "Invalid credentials"
}
```

---

## Public Endpoints (No Auth Required)

### Register Callsign in Queue

**Purpose**: Add callsign to pileup queue  
**Send**:
```json
{
  "type": "register_callsign",
  "request_id": "reg_001",
  "callsign": "EA1ABC"
}
```

**Receive (Success)**:
```json
{
  "type": "success",
  "request_id": "reg_001",
  "message": "Callsign registered successfully",
  "data": {
    "callsign": "EA1ABC",
    "position": 3,
    "total_queue": 3
  }
}
```

### Get Queue Status

**Purpose**: Query current system state  
**Send**:
```json
{
  "type": "get_queue_status",
  "request_id": "status_001"
}
```

**Receive**:
```json
{
  "type": "success",
  "request_id": "status_001",
  "data": {
    "system_active": true,
    "queue_size": 2,
    "max_queue_size": 4,
    "current_qso": {
      "callsign": "EA1ABC",
      "timestamp": "2025-07-23T10:28:00Z"
    }
  }
}
```

---

## Admin Endpoints (Auth Required)

### Send QSO Data

**Purpose**: Send completed QSO to system  
**Send**:
```json
{
  "type": "admin_send_qso",
  "request_id": "qso_001",
  "session_token": "your_token",
  "callsign": "EA1ABC",
  "frequency": "14.205",
  "mode": "USB",
  "rst_sent": "59",
  "rst_received": "59",
  "timestamp": "2025-07-23T10:30:00Z"
}
```

**Receive**:
```json
{
  "type": "success",
  "request_id": "qso_001",
  "message": "QSO processed successfully",
  "data": {
    "callsign": "EA1ABC",
    "processed_as": "external_qso",
    "current_qso_set": true
  }
}
```

### Work Next User

**Purpose**: Advance queue to next person  
**Send**:
```json
{
  "type": "admin_work_next",
  "request_id": "work_001",
  "session_token": "your_token"
}
```

**Receive**:
```json
{
  "type": "success",
  "request_id": "work_001",
  "message": "Next user activated for QSO",
  "data": {
    "callsign": "DL1ABC",
    "remaining_queue": 1
  }
}
```

### Complete Current QSO

**Purpose**: Clear current QSO without advancing queue  
**Send**:
```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_001",
  "session_token": "your_token"
}
```

**Receive**:
```json
{
  "type": "success",
  "request_id": "complete_001",
  "message": "Current QSO completed successfully",
  "data": {
    "completed_callsign": "EA1ABC",
    "current_qso_cleared": true
  }
}
```

### Toggle System Status

**Purpose**: Enable/disable system (automatic toggle)  
**Send**:
```json
{
  "type": "admin_toggle_system",
  "request_id": "toggle_001",
  "session_token": "your_token"
}
```

**Receive (Activated)**:
```json
{
  "type": "success",
  "request_id": "toggle_001",
  "message": "System activated successfully",
  "data": {
    "system_active": true,
    "previous_state": false
  }
}
```

**Receive (Deactivated)**:
```json
{
  "type": "success",
  "request_id": "toggle_001",
  "message": "System deactivated successfully",
  "data": {
    "system_active": false,
    "previous_state": true,
    "queue_cleared": true
  }
}
```

### Clear Queue

**Purpose**: Remove all queue entries  
**Send**:
```json
{
  "type": "admin_clear_queue",
  "request_id": "clear_001",
  "session_token": "your_token"
}
```

**Receive**:
```json
{
  "type": "success",
  "request_id": "clear_001",
  "message": "Queue cleared successfully",
  "data": {
    "cleared_count": 3,
    "queue_size": 0
  }
}
```

### Heartbeat/Ping

**Purpose**: Keep connection alive  
**Send**:
```json
{
  "type": "ping",
  "request_id": "ping_001",
  "session_token": "your_token"
}
```

**Receive**:
```json
{
  "type": "pong",
  "request_id": "ping_001",
  "timestamp": "2025-07-23T10:30:00Z"
}
```

---

## Real-time Broadcasts

**Note**: These are automatically sent to all connected clients when events occur.

### Queue Update

**Trigger**: Queue changes (registration, user worked, cleared)  
**Receive**:
```json
{
  "type": "queue_update",
  "timestamp": "2025-07-23T10:30:00Z",
  "data": {
    "total": 1,
    "max_size": 4,
    "change_type": "user_worked",
    "affected_callsign": "DL1ABC"
  }
}
```

### QSO Update

**Trigger**: Current QSO changes  
**Receive**:
```json
{
  "type": "qso_update",
  "timestamp": "2025-07-23T10:30:00Z",
  "data": {
    "callsign": "EA1ABC",
    "started_at": "2025-07-23T10:30:00Z",
    "source": "logging_software"
  }
}
```

### System Status Update

**Trigger**: System activated/deactivated  
**Receive**:
```json
{
  "type": "system_status_update",
  "timestamp": "2025-07-23T10:30:00Z",
  "data": {
    "active": true,
    "changed_by": "admin"
  }
}
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `AUTHENTICATION_REQUIRED` | Missing/invalid token | Re-authenticate |
| `AUTHENTICATION_FAILED` | Wrong credentials | Check username/password |
| `SESSION_EXPIRED` | Token expired | Re-authenticate |
| `INVALID_REQUEST` | Bad message format | Check required fields |
| `INVALID_CALLSIGN` | Bad callsign format | Use valid amateur callsign |
| `SYSTEM_INACTIVE` | System disabled | Activate system first |
| `QUEUE_FULL` | Queue at capacity | Wait or clear queue |
| `QUEUE_EMPTY` | No users to work | Wait for registrations |
| `ALREADY_IN_QUEUE` | Duplicate callsign | Callsign already registered |
| `SYSTEM_ERROR` | Server error | Check server logs |

---

## Quick Integration Pattern

### 1. Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');
```

### 2. Authenticate
```javascript
ws.send(JSON.stringify({
  type: "auth_request",
  request_id: "auth_" + Date.now(),
  username: "admin",
  password: "password"
}));
```

### 3. Handle Messages
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "auth_response" && data.success) {
    sessionToken = data.session_token;
  }
  else if (data.type === "success") {
    console.log("Operation successful:", data.message);
  }
  else if (data.type === "error") {
    console.error("Error:", data.error_code, data.message);
  }
  else if (data.type === "queue_update") {
    // Handle queue changes
  }
  else if (data.type === "qso_update") {
    // Handle QSO changes
  }
  else if (data.type === "system_status_update") {
    // Handle system status changes
  }
};
```

### 4. Send Operations
```javascript
// Send QSO
ws.send(JSON.stringify({
  type: "admin_send_qso",
  request_id: "qso_" + Date.now(),
  session_token: sessionToken,
  callsign: "EA1ABC",
  frequency: "14.205",
  mode: "USB",
  rst_sent: "59",
  rst_received: "59",
  timestamp: new Date().toISOString()
}));

// Toggle system
ws.send(JSON.stringify({
  type: "admin_toggle_system",
  request_id: "toggle_" + Date.now(),
  session_token: sessionToken
}));
```

---

## Best Practices

1. **Always use unique request_id**: Use timestamp or UUID
2. **Implement timeout handling**: Don't wait forever for responses
3. **Handle reconnection**: WebSocket can disconnect
4. **Validate responses**: Check for success/error types
5. **Keep session alive**: Send ping every 30 seconds
6. **Store credentials securely**: Don't hardcode passwords
7. **Handle broadcasts**: Listen for real-time updates

---

## Common Issues

**Problem**: No response to requests  
**Solution**: Check request_id uniqueness and session token validity

**Problem**: Authentication fails  
**Solution**: Verify ADMIN_USERNAME and ADMIN_PASSWORD environment variables

**Problem**: "System inactive" errors  
**Solution**: Use admin_toggle_system to activate before operations

**Problem**: Connection drops  
**Solution**: Implement heartbeat (ping/pong) and reconnection logic

---

**End of Guide** - For detailed examples see `WS-All.prd`
