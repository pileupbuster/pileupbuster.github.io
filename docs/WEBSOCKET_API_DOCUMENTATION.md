# WebSocket API Documentation for Pileup Buster

This document describes the WebSocket API for Pileup Buster, which provides unified authentication and operations through WebSocket connections.

## Connection

Connect to the WebSocket endpoint at:
```
ws://localhost:8000/api/ws
```

## Message Format

All messages are JSON with the following structure:

```json
{
  "type": "message_type",
  "request_id": "unique_id",  // Optional for requests, required for responses
  "timestamp": "2025-01-20T10:30:00",  // Auto-generated
  "data": {}  // Message-specific data
}
```

## Authentication

### 1. Authentication Request

```json
{
  "type": "auth_request",
  "request_id": "auth_001",
  "username": "admin",
  "password": "your_password"
}
```

### 2. Authentication Response

**Success:**
```json
{
  "type": "auth_response",
  "request_id": "auth_001",
  "authenticated": true,
  "session_token": "abc123...",
  "message": "Authentication successful",
  "expires_at": "2025-01-21T10:30:00"
}
```

**Failure:**
```json
{
  "type": "auth_response",
  "request_id": "auth_001",
  "authenticated": false,
  "message": "Invalid credentials"
}
```

## Admin Operations (Require Authentication)

All admin operations require a `session_token` obtained from successful authentication.

### Get Queue Status

```json
{
  "type": "admin_get_queue",
  "request_id": "queue_001",
  "session_token": "abc123..."
}
```

**Response:**
```json
{
  "type": "success",
  "request_id": "queue_001",
  "message": "Queue retrieved successfully",
  "data": {
    "queue": [
      {
        "callsign": "W1ABC",
        "timestamp": "2025-01-20T10:30:00",
        "position": 1,
        "qrz": {
          "name": "John Doe",
          "address": "United States",
          "dxcc_name": "United States"
        }
      }
    ],
    "total": 1,
    "max_size": 4,
    "system_active": true
  }
}
```

### Complete Current QSO

```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_001",
  "session_token": "abc123..."
}
```

### Work Next Person in Queue

```json
{
  "type": "admin_work_next",
  "request_id": "next_001",
  "session_token": "abc123..."
}
```

### Start QSO from Logging Software

```json
{
  "type": "admin_start_qso",
  "request_id": "start_001",
  "session_token": "abc123...",
  "callsign": "W1ABC",
  "frequency_mhz": 14.315,
  "mode": "CW",
  "source": "direct"
}
```

### Set Frequency

```json
{
  "type": "admin_set_frequency",
  "request_id": "freq_001",
  "session_token": "abc123...",
  "frequency": "14.315"
}
```

### Clear Frequency

```json
{
  "type": "admin_clear_frequency",
  "request_id": "freq_clear_001",
  "session_token": "abc123..."
}
```

### Toggle System Status

```json
{
  "type": "admin_toggle_system",
  "request_id": "system_001",
  "session_token": "abc123...",
  "active": true
}
```

## Public Operations (No Authentication Required)

### Register Callsign

```json
{
  "type": "register_callsign",
  "request_id": "register_001",
  "callsign": "W1ABC"
}
```

### Get Queue Status (Public)

```json
{
  "type": "get_queue_status",
  "request_id": "queue_pub_001"
}
```

### Get Current QSO

```json
{
  "type": "get_current_qso",
  "request_id": "qso_001"
}
```

## Real-time Broadcasts

The server automatically broadcasts these messages to all connected clients when changes occur:

### Queue Update

```json
{
  "type": "queue_update",
  "timestamp": "2025-01-20T10:30:00",
  "queue": [...],
  "total": 2,
  "max_size": 4,
  "system_active": true
}
```

### QSO Update

```json
{
  "type": "qso_update",
  "timestamp": "2025-01-20T10:30:00",
  "current_qso": {
    "callsign": "W1ABC",
    "timestamp": "2025-01-20T10:30:00",
    "qrz": {...},
    "metadata": {
      "source": "queue",
      "bridge_initiated": false
    }
  }
}
```

### System Status Update

```json
{
  "type": "system_status_update",
  "timestamp": "2025-01-20T10:30:00",
  "active": true
}
```

## Error Handling

Error responses follow this format:

```json
{
  "type": "error",
  "request_id": "original_request_id",
  "error_code": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {}
}
```

### Error Codes

- `AUTH_REQUIRED` - Authentication required for this operation
- `INVALID_CREDENTIALS` - Username/password incorrect
- `SESSION_EXPIRED` - Session token expired or invalid
- `PERMISSION_DENIED` - User lacks required permissions
- `INVALID_FORMAT` - Message format is invalid
- `INVALID_REQUEST` - Request parameters are invalid
- `SYSTEM_ERROR` - Internal server error
- `CALLSIGN_INVALID` - Callsign format is invalid
- `QUEUE_FULL` - Queue has reached maximum capacity
- `SYSTEM_INACTIVE` - System is currently inactive

## Keepalive/Ping

Send ping messages to keep the connection alive:

```json
{
  "type": "ping"
}
```

Response:
```json
{
  "type": "pong",
  "timestamp": "2025-01-20T10:30:00"
}
```

## QT6 Implementation Example

Here's a complete QT6 implementation example for your logging software:

```cpp
#include <QWebSocket>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>

class PileupBusterWebSocketClient : public QObject {
    Q_OBJECT

private:
    QWebSocket* webSocket;
    QString sessionToken;
    QTimer* pingTimer;
    int requestCounter = 0;

public:
    PileupBusterWebSocketClient(const QString& url) {
        webSocket = new QWebSocket(QString(), QWebSocketProtocol::VersionLatest, this);
        
        // Setup connections
        connect(webSocket, &QWebSocket::connected, this, &PileupBusterWebSocketClient::onConnected);
        connect(webSocket, &QWebSocket::textMessageReceived, this, &PileupBusterWebSocketClient::onMessageReceived);
        connect(webSocket, &QWebSocket::disconnected, this, &PileupBusterWebSocketClient::onDisconnected);
        
        // Setup ping timer
        pingTimer = new QTimer(this);
        connect(pingTimer, &QTimer::timeout, this, &PileupBusterWebSocketClient::sendPing);
        
        // Connect to server
        webSocket->open(QUrl(url));
    }

    void authenticate(const QString& username, const QString& password) {
        QJsonObject message;
        message["type"] = "auth_request";
        message["request_id"] = QString("auth_%1").arg(++requestCounter);
        message["username"] = username;
        message["password"] = password;
        
        sendMessage(message);
    }

    void startQsoFromLoggingSoftware(const QString& callsign, double frequency, const QString& mode) {
        if (sessionToken.isEmpty()) {
            qWarning() << "Not authenticated";
            return;
        }
        
        QJsonObject message;
        message["type"] = "admin_start_qso";
        message["request_id"] = QString("start_qso_%1").arg(++requestCounter);
        message["session_token"] = sessionToken;
        message["callsign"] = callsign;
        message["frequency_mhz"] = frequency;
        message["mode"] = mode;
        message["source"] = "direct";
        
        sendMessage(message);
    }

    void completeCurrentQso() {
        if (sessionToken.isEmpty()) {
            qWarning() << "Not authenticated";
            return;
        }
        
        QJsonObject message;
        message["type"] = "admin_complete_qso";
        message["request_id"] = QString("complete_%1").arg(++requestCounter);
        message["session_token"] = sessionToken;
        
        sendMessage(message);
    }

    void workNextInQueue() {
        if (sessionToken.isEmpty()) {
            qWarning() << "Not authenticated";
            return;
        }
        
        QJsonObject message;
        message["type"] = "admin_work_next";
        message["request_id"] = QString("work_next_%1").arg(++requestCounter);
        message["session_token"] = sessionToken;
        
        sendMessage(message);
    }

private slots:
    void onConnected() {
        qDebug() << "WebSocket connected";
        pingTimer->start(30000); // Ping every 30 seconds
    }

    void onDisconnected() {
        qDebug() << "WebSocket disconnected";
        pingTimer->stop();
        sessionToken.clear();
    }

    void onMessageReceived(const QString& message) {
        QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
        QJsonObject obj = doc.object();
        
        QString type = obj["type"].toString();
        
        if (type == "auth_response") {
            handleAuthResponse(obj);
        } else if (type == "success") {
            handleSuccess(obj);
        } else if (type == "error") {
            handleError(obj);
        } else if (type == "queue_update") {
            handleQueueUpdate(obj);
        } else if (type == "qso_update") {
            handleQsoUpdate(obj);
        } else if (type == "pong") {
            // Keepalive response
        }
    }

    void handleAuthResponse(const QJsonObject& obj) {
        bool authenticated = obj["authenticated"].toBool();
        if (authenticated) {
            sessionToken = obj["session_token"].toString();
            qDebug() << "Authentication successful";
            emit authenticationSuccessful();
        } else {
            qDebug() << "Authentication failed:" << obj["message"].toString();
            emit authenticationFailed(obj["message"].toString());
        }
    }

    void handleSuccess(const QJsonObject& obj) {
        QString message = obj["message"].toString();
        qDebug() << "Operation successful:" << message;
        emit operationSuccessful(message);
    }

    void handleError(const QJsonObject& obj) {
        QString errorCode = obj["error_code"].toString();
        QString message = obj["message"].toString();
        qDebug() << "Error:" << errorCode << "-" << message;
        emit operationError(errorCode, message);
    }

    void handleQueueUpdate(const QJsonObject& obj) {
        // Handle queue updates
        emit queueUpdated(obj);
    }

    void handleQsoUpdate(const QJsonObject& obj) {
        // Handle QSO updates
        emit qsoUpdated(obj);
    }

    void sendPing() {
        QJsonObject ping;
        ping["type"] = "ping";
        sendMessage(ping);
    }

    void sendMessage(const QJsonObject& message) {
        QJsonDocument doc(message);
        webSocket->sendTextMessage(doc.toJson(QJsonDocument::Compact));
    }

signals:
    void authenticationSuccessful();
    void authenticationFailed(const QString& reason);
    void operationSuccessful(const QString& message);
    void operationError(const QString& errorCode, const QString& message);
    void queueUpdated(const QJsonObject& queueData);
    void qsoUpdated(const QJsonObject& qsoData);
};
```

## Usage Example

```cpp
// Create client
PileupBusterWebSocketClient* client = new PileupBusterWebSocketClient("ws://localhost:8000/api/ws");

// Connect signals
connect(client, &PileupBusterWebSocketClient::authenticationSuccessful, [=]() {
    qDebug() << "Ready to use admin functions";
    
    // Now you can call admin functions
    client->startQsoFromLoggingSoftware("W1ABC", 14.315, "CW");
});

// Authenticate
client->authenticate("admin", "your_password");
```

This WebSocket implementation provides a unified interface that eliminates the need to mix protocols. Your QT6 application can authenticate once and then perform all operations through the same WebSocket connection, including receiving real-time updates.
