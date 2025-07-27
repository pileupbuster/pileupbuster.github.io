# WebSocket Authentication Requirements for PileupBuster

## Overview
This document outlines the WebSocket authentication requirements for the PileupBuster web application to work with the PBLog Qt6 client.

## Current Implementation Status
- **Client Side (PBLog)**: ✅ Complete - Pure WebSocket implementation with multiple auth fallback methods
- **Server Side (PileupBuster)**: ⚠️ Needs WebSocket authentication implementation

## WebSocket Authentication Methods to Implement

### Method 1: Authorization Header (Preferred)
```javascript
// During WebSocket handshake, check for Authorization header
const authHeader = request.headers.authorization;
if (authHeader && authHeader.startsWith('Basic ')) {
    const credentials = Buffer.from(authHeader.slice(6), 'base64').toString();
    const [username, password] = credentials.split(':');
    // Validate against ADMIN_USERNAME and ADMIN_PASSWORD
}
```

### Method 2: URL-based Authentication (Fallback)
```javascript
// Support authentication in WebSocket URL: ws://username:password@host:port/ws
const url = new URL(request.url, `ws://${request.headers.host}`);
if (url.username && url.password) {
    // Validate credentials
}
```

### Method 3: Query Parameters (Fallback)
```javascript
// Support authentication via query parameters: ws://host:port/ws?username=user&password=pass
const url = new URL(request.url, `ws://${request.headers.host}`);
const params = new URLSearchParams(url.search);
const username = params.get('username');
const password = params.get('password');
```

## Required WebSocket Operations

### Admin Operations (Require Authentication)
1. **admin.logging_direct** - Start QSO from logging software
   ```json
   {
     "type": "request",
     "id": "uuid",
     "operation": "admin.logging_direct",
     "data": {
       "callsign": "EA1ABC",
       "frequency_mhz": 14.205,
       "mode": "SSB"
     }
   }
   ```

2. **admin.qso.complete** - Complete current QSO
3. **admin.queue** - Get queue status
4. **system.ping** - Connection verification

### Public Operations (No Authentication Required)
1. **queue.register** - Register for queue (public)
2. **system.heartbeat** - Keep connection alive

## Response Format
```json
{
  "type": "response",
  "id": "request_uuid",
  "success": true,
  "data": { ... },
  "error": "error_message_if_failed"
}
```

## Event Streaming
After successful authentication, the WebSocket should stream real-time events:
- **current_qso** - Current QSO state changes
- **queue_update** - Queue status updates
- **system_status** - System status changes
- **frequency_update** - Frequency changes
- **split_update** - Split frequency changes
- **keepalive** - Connection health check

## Environment Variables Required
```bash
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

## Implementation Notes
1. **Security**: Use the same HTTP Basic Authentication credentials for WebSocket as for HTTP REST API
2. **Fallback**: Implement multiple authentication methods for maximum compatibility
3. **Error Handling**: Return proper error responses for authentication failures
4. **Connection Management**: Handle connection drops and reconnection gracefully

## Qt6 Client Capabilities
The PBLog client already implements:
- ✅ Multiple authentication fallback methods
- ✅ Automatic reconnection with exponential backoff
- ✅ Request/response tracking with timeouts
- ✅ Real-time event processing
- ✅ Proper error handling and user feedback

## Testing
Once implemented, test with:
1. Valid credentials → Should connect and allow admin operations
2. Invalid credentials → Should reject with 401/403
3. No credentials → Should reject admin operations but allow public operations
4. Connection drops → Should reconnect automatically
