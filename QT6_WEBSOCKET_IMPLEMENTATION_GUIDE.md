# WebSocket Implementation Instructions for PBLog Qt6 Client

## Good News! ✅ 
The PileupBuster WebSocket API is **already fully implemented** and meets all your requirements. You can implement a pure WebSocket solution without any protocol mixing.

## WebSocket Endpoint
```
ws://localhost:8000/api/ws
```

## Authentication Implementation for PBLog

### ✅ Method 1: Message-Based Authentication (Recommended)
**This is the cleanest approach - authenticate after connecting:**

```cpp
// 1. Connect to WebSocket
webSocket->open(QUrl("ws://localhost:8000/api/ws"));

// 2. Send authentication message after connection
QJsonObject authMessage;
authMessage["type"] = "auth_request";
authMessage["request_id"] = "auth_001";
authMessage["username"] = "your_admin_username";  // From env var
authMessage["password"] = "your_admin_password";  // From env var

// 3. Receive session token
// Response will contain session_token for all future operations
```

### ✅ All Required Operations Are Implemented

#### 1. admin.logging_direct → `admin_start_qso`
```json
{
  "type": "admin_start_qso",
  "request_id": "start_001",
  "session_token": "your_session_token",
  "callsign": "EA1ABC",
  "frequency_mhz": 14.205,
  "mode": "SSB",
  "source": "direct"
}
```

#### 2. admin.qso.complete → `admin_complete_qso`
```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_001",
  "session_token": "your_session_token"
}
```

#### 3. admin.queue → `admin_get_queue`
```json
{
  "type": "admin_get_queue",
  "request_id": "queue_001",
  "session_token": "your_session_token"
}
```

#### 4. system.ping → `ping`
```json
{
  "type": "ping"
}
```

### ✅ Real-time Events (Auto-streamed)
After authentication, you automatically receive:
- `queue_update` - Queue status changes
- `qso_update` - Current QSO changes  
- `system_status_update` - System status changes

### ✅ Response Format
All responses follow this format:
```json
{
  "type": "success",
  "request_id": "your_request_id",
  "message": "Operation successful",
  "data": { ... }
}
```

Or for errors:
```json
{
  "type": "error",
  "request_id": "your_request_id",
  "error_code": "ERROR_CODE",
  "message": "Error description"
}
```

## Complete Qt6 Implementation Example

```cpp
class PileupBusterWebSocketClient : public QObject {
    Q_OBJECT

private:
    QWebSocket* webSocket;
    QString sessionToken;
    QString adminUsername;
    QString adminPassword;
    int requestCounter = 0;

public:
    PileupBusterWebSocketClient(const QString& url, const QString& username, const QString& password) 
        : adminUsername(username), adminPassword(password) {
        
        webSocket = new QWebSocket(QString(), QWebSocketProtocol::VersionLatest, this);
        
        connect(webSocket, &QWebSocket::connected, this, &PileupBusterWebSocketClient::onConnected);
        connect(webSocket, &QWebSocket::textMessageReceived, this, &PileupBusterWebSocketClient::onMessageReceived);
        
        webSocket->open(QUrl(url));
    }

    void onConnected() {
        qDebug() << "Connected to PileupBuster WebSocket";
        
        // Immediately authenticate after connection
        QJsonObject authMessage;
        authMessage["type"] = "auth_request";
        authMessage["request_id"] = QString("auth_%1").arg(++requestCounter);
        authMessage["username"] = adminUsername;
        authMessage["password"] = adminPassword;
        
        sendMessage(authMessage);
    }

    void onMessageReceived(const QString& message) {
        QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
        QJsonObject obj = doc.object();
        
        QString type = obj["type"].toString();
        
        if (type == "auth_response") {
            bool authenticated = obj["authenticated"].toBool();
            if (authenticated) {
                sessionToken = obj["session_token"].toString();
                qDebug() << "Authentication successful!";
                emit authenticationSuccessful();
            } else {
                qDebug() << "Authentication failed:" << obj["message"].toString();
                emit authenticationFailed();
            }
        } 
        else if (type == "success") {
            handleSuccessResponse(obj);
        }
        else if (type == "error") {
            handleErrorResponse(obj);
        }
        else if (type == "queue_update") {
            emit queueUpdated(obj);
        }
        else if (type == "qso_update") {
            emit qsoUpdated(obj);
        }
        else if (type == "system_status_update") {
            emit systemStatusUpdated(obj);
        }
        else if (type == "pong") {
            // Keepalive response
        }
    }

    // Admin Operations
    void startQsoFromLogging(const QString& callsign, double frequency, const QString& mode) {
        if (sessionToken.isEmpty()) {
            qWarning() << "Not authenticated";
            return;
        }
        
        QJsonObject message;
        message["type"] = "admin_start_qso";
        message["request_id"] = QString("start_%1").arg(++requestCounter);
        message["session_token"] = sessionToken;
        message["callsign"] = callsign;
        message["frequency_mhz"] = frequency;
        message["mode"] = mode;
        message["source"] = "direct";
        
        sendMessage(message);
    }

    void completeCurrentQso() {
        if (sessionToken.isEmpty()) return;
        
        QJsonObject message;
        message["type"] = "admin_complete_qso";
        message["request_id"] = QString("complete_%1").arg(++requestCounter);
        message["session_token"] = sessionToken;
        
        sendMessage(message);
    }

    void getQueueStatus() {
        if (sessionToken.isEmpty()) return;
        
        QJsonObject message;
        message["type"] = "admin_get_queue";
        message["request_id"] = QString("queue_%1").arg(++requestCounter);
        message["session_token"] = sessionToken;
        
        sendMessage(message);
    }

    void ping() {
        QJsonObject message;
        message["type"] = "ping";
        sendMessage(message);
    }

private:
    void sendMessage(const QJsonObject& message) {
        QJsonDocument doc(message);
        webSocket->sendTextMessage(doc.toJson(QJsonDocument::Compact));
    }

signals:
    void authenticationSuccessful();
    void authenticationFailed();
    void queueUpdated(const QJsonObject& data);
    void qsoUpdated(const QJsonObject& data);
    void systemStatusUpdated(const QJsonObject& data);
};
```

## Usage Instructions

1. **Connect and Authenticate:**
```cpp
PileupBusterWebSocketClient* client = new PileupBusterWebSocketClient(
    "ws://localhost:8000/api/ws", 
    "admin_username",  // From environment
    "admin_password"   // From environment
);

connect(client, &PileupBusterWebSocketClient::authenticationSuccessful, [=]() {
    qDebug() << "Ready to use admin functions";
    // Now you can call any admin function
});
```

2. **Start QSO from Logging Software:**
```cpp
client->startQsoFromLogging("EA1ABC", 14.205, "SSB");
```

3. **Complete QSO:**
```cpp
client->completeCurrentQso();
```

4. **Get Queue Status:**
```cpp
client->getQueueStatus();
```

## Key Points

- ✅ **Pure WebSocket**: No HTTP mixing required
- ✅ **Single Connection**: One WebSocket handles everything
- ✅ **Real-time Updates**: Automatic event streaming
- ✅ **All Operations Available**: Everything your Qt6 client needs
- ✅ **Proper Authentication**: Session-based with tokens
- ✅ **Error Handling**: Comprehensive error responses

## Environment Variables
Make sure PileupBuster has these set:
```bash
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

The WebSocket API is ready to use right now - no changes needed on the PileupBuster side!
