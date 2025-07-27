# `admin_cancel_qso` WebSocket Endpoint - Simple Integration Guide

## 🎯 **Purpose**
Cancel/abort the current QSO when it was started by mistake or shouldn't continue.

## 📡 **WebSocket Message**

### **Send (Your App → Pileup Buster)**
```json
{
  "type": "admin_cancel_qso",
  "request_id": "cancel_001",
  "session_token": "your_session_token"
}
```

### **Receive - Success Response**
```json
{
  "type": "success",
  "request_id": "cancel_001",
  "message": "QSO with EA1ABC cancelled successfully",
  "data": {
    "cancelled_qso": {
      "callsign": "EA1ABC",
      "timestamp": "2025-07-25T14:30:00Z",
      "qrz": {
        "name": "John Smith",
        "address": "Madrid, Spain"
      }
    }
  }
}
```

### **Receive - No QSO Active**
```json
{
  "type": "success",
  "request_id": "cancel_001", 
  "message": "No active QSO to cancel",
  "data": {
    "cancelled_qso": null
  }
}
```

### **Receive - Error**
```json
{
  "type": "error",
  "request_id": "cancel_001",
  "error_code": "AUTH_REQUIRED",
  "message": "Authentication required"
}
```

## 🔧 **Qt6 Integration Example**

```cpp
// In your WebSocket handler class
void cancelCurrentQso() {
    if (!sessionToken.isEmpty()) {
        QJsonObject message;
        message["type"] = "admin_cancel_qso";
        message["request_id"] = "cancel_" + QString::number(QDateTime::currentMSecsSinceEpoch());
        message["session_token"] = sessionToken;
        
        QJsonDocument doc(message);
        webSocket->sendTextMessage(doc.toJson(QJsonDocument::Compact));
    }
}

// In your message handler
void handleWebSocketMessage(const QString& message) {
    QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
    QJsonObject obj = doc.object();
    
    QString type = obj["type"].toString();
    QString requestId = obj["request_id"].toString();
    
    if (type == "success" && requestId.startsWith("cancel_")) {
        QString msg = obj["message"].toString();
        QJsonObject data = obj["data"].toObject();
        QJsonObject cancelledQso = data["cancelled_qso"].toObject();
        
        if (!cancelledQso.isEmpty()) {
            QString callsign = cancelledQso["callsign"].toString();
            qDebug() << "QSO with" << callsign << "cancelled successfully";
            // Update your UI - clear current QSO display
            clearCurrentQsoDisplay();
        } else {
            qDebug() << "No active QSO was cancelled";
        }
    }
}
```

## ⚡ **Real-time Updates**
After cancelling, **all connected clients** automatically receive:
```json
{
  "type": "qso_update",
  "timestamp": "2025-07-25T14:30:00Z",
  "current_qso": null
}
```

## 🎛️ **When to Use**
- **Cancel**: User accidentally started QSO with wrong callsign
- **Cancel**: Discovered station is duplicate/invalid 
- **Cancel**: QSO interrupted and shouldn't be logged

## 🔗 **Authentication Required**
You must have a valid `session_token` from successful WebSocket authentication before using this endpoint.

That's it! Simple one-message operation to cancel any active QSO. 🚀
