# 🔧 **Pileup Buster System Status Management via WebSocket**

This document explains how to check and change the active/disabled status of the Pileup Buster system using WebSocket endpoints. This is designed for AI integration and external logging software control.

## **1. 📊 Get System Status (Query Current State)**

**Endpoint**: WebSocket message type `admin_get_status`

**Purpose**: Check if the Pileup Buster system is currently active (accepting new registrations) or disabled

**Authentication**: Requires valid session token

**Request Format**:
```json
{
  "type": "admin_get_status",
  "request_id": "status_query_001",
  "session_token": "your_session_token_here"
}
```

**Success Response**:
```json
{
  "type": "success",
  "request_id": "status_query_001",
  "message": "System status retrieved successfully",
  "data": {
    "system_active": true,
    "registration_enabled": true,
    "queue_size": 2,
    "max_queue_size": 4,
    "current_qso": {
      "callsign": "EA1ABC",
      "name": "John Smith",
      "location": "Madrid, Spain"
    }
  }
}
```

**Error Response**:
```json
{
  "type": "error",
  "request_id": "status_query_001",
  "error_code": "AUTHENTICATION_REQUIRED",
  "message": "Valid session token required"
}
```

## **2. 🔄 Toggle System Status (Enable/Disable)**

**Endpoint**: WebSocket message type `admin_toggle_system`

**Purpose**: Automatically toggle the Pileup Buster system between active/inactive states

**Authentication**: Requires valid session token

**How it works**: The system automatically detects the current status and flips it:
- If currently **active** → becomes **inactive**
- If currently **inactive** → becomes **active**

**Request Format**:
```json
{
  "type": "admin_toggle_system",
  "request_id": "toggle_001",
  "session_token": "your_session_token_here"
}
```

**Note**: No `active` field is required - the system automatically toggles the current state.

**Success Response (System Enabled)**:
```json
{
  "type": "success",
  "request_id": "toggle_001",
  "message": "System activated successfully",
  "data": {
    "system_active": true,
    "registration_enabled": true,
    "previous_state": false,
    "changed_by": "logging_software",
    "timestamp": "2025-01-15T10:30:00"
  }
}
```

**Success Response (System Disabled)**:
```json
{
  "type": "success",
  "request_id": "toggle_001",
  "message": "System deactivated successfully",
  "data": {
    "system_active": false,
    "registration_enabled": false,
    "previous_state": true,
    "changed_by": "logging_software",
    "timestamp": "2025-01-15T10:30:00"
  }
}
```

## **3. 🔔 Real-time Status Updates (Automatic)**

**Purpose**: When system status changes, all connected WebSocket clients automatically receive updates

**Auto-broadcast Message**:
```json
{
  "type": "system_status_update",
  "timestamp": "2025-07-21T12:00:00Z",
  "data": {
    "system_active": true,
    "registration_enabled": true,
    "changed_by": "admin",
    "reason": "System toggled via WebSocket"
  }
}
```

## **4. 📝 Complete Example Workflow**

Here's how to implement status management in Qt6/C++:

```cpp
// 1. Check current status
void checkSystemStatus() {
    QJsonObject request;
    request["type"] = "admin_get_status";
    request["request_id"] = QString("status_%1").arg(QDateTime::currentMSecsSinceEpoch());
    request["session_token"] = sessionToken;
    
    webSocket->sendTextMessage(QJsonDocument(request).toJson());
}

// 2. Toggle system status
void toggleSystemStatus() {
    QJsonObject request;
    request["type"] = "admin_toggle_system";
    request["request_id"] = QString("toggle_%1").arg(QDateTime::currentMSecsSinceEpoch());
    request["session_token"] = sessionToken;
    
    webSocket->sendTextMessage(QJsonDocument(request).toJson());
}

// 3. Handle responses
void handleWebSocketMessage(const QString& message) {
    QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
    QJsonObject obj = doc.object();
    
    QString type = obj["type"].toString();
    
    if (type == "success") {
        QString requestId = obj["request_id"].toString();
        QJsonObject data = obj["data"].toObject();
        
        if (requestId.startsWith("status_")) {
            // Status query response
            bool systemActive = data["system_active"].toBool();
            int queueSize = data["queue_size"].toInt();
            emit systemStatusReceived(systemActive, queueSize);
        }
        else if (requestId.startsWith("toggle_")) {
            // Toggle response
            bool newState = data["system_active"].toBool();
            bool previousState = data["previous_state"].toBool();
            emit systemToggled(newState, previousState);
        }
    }
    else if (type == "system_status_update") {
        // Real-time status update
        QJsonObject data = obj["data"].toObject();
        bool systemActive = data["system_active"].toBool();
        emit systemStatusChanged(systemActive);
    }
}
```

## **5. 🎯 Key Points for Implementation**

### **Status States**
- `system_active: true` = System is running, accepts new registrations
- `system_active: false` = System is disabled, rejects new registrations

### **Authentication Requirements**
- Both operations require a valid session token from WebSocket authentication
- Invalid/expired tokens return `AUTHENTICATION_REQUIRED` error
- See [WEBSOCKET_API_DOCUMENTATION.md](docs/WEBSOCKET_API_DOCUMENTATION.md) for authentication details

### **Real-time Updates**
- All WebSocket clients automatically receive `system_status_update` when status changes
- No polling needed - updates are pushed immediately
- Multiple clients stay synchronized automatically

### **Error Handling**
- Always check for `type: "error"` responses
- Common error codes:
  - `AUTHENTICATION_REQUIRED` - Invalid or missing session token
  - `INVALID_REQUEST` - Malformed request message
  - `SYSTEM_ERROR` - Internal server error

### **Request ID Best Practices**
- Use unique request IDs to correlate responses with requests
- Recommended format: `status_<timestamp>` or `toggle_<timestamp>`
- Example: `status_1642780800000` or `toggle_1642780800001`

### **Connection Requirements**
- WebSocket endpoint: `ws://localhost:8000/api/ws`
- Must authenticate first using `auth_request` message type
- Session token expires after 24 hours

## **6. 📋 Integration Checklist**

Before implementing system status control:

- [ ] WebSocket connection established to `ws://localhost:8000/api/ws`
- [ ] Successfully authenticated and received session token
- [ ] Request ID generation system in place
- [ ] Error handling for authentication failures
- [ ] Message parsing for JSON responses
- [ ] Event handlers for real-time status updates

## **7. 🚀 Complete Integration Flow**

1. **Connect** to WebSocket endpoint
2. **Authenticate** with admin credentials
3. **Store** session token for subsequent requests
4. **Query** current system status using `admin_get_status`
5. **Toggle** system as needed using `admin_toggle_system`
6. **Listen** for `system_status_update` broadcasts
7. **Handle** errors and re-authenticate if token expires

This provides complete programmatic control over the Pileup Buster system status through a clean WebSocket API interface.
