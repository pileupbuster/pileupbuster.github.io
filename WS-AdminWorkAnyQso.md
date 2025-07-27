# 🎯 **Admin Work Specific QSO - WebSocket API Guide**

**Document Version**: 1.0  
**Last Updated**: July 24, 2025  
**Target Audience**: External Logging Software Integration (Qt6, C++, Python, etc.)

---

## 📋 **Overview**

The `admin_work_specific` endpoint allows your logging application to work any specific callsign directly from the queue, bypassing the normal FIFO (First-In-First-Out) order. This is particularly useful when you need to work stations out of order for operational reasons.

### **Key Features**
- **Direct Callsign Selection**: Work any callsign currently in the queue
- **Graceful Duplicate Handling**: If the callsign is already the current QSO, the operation succeeds without changes
- **Automatic Queue Management**: Removes the callsign from queue and sets it as current QSO
- **Real-time Broadcasting**: All connected clients receive updates about the change
- **Position Tracking**: Response includes the original queue position for reference

---

## 🚀 **Usage Scenarios**

### **When to Use This Endpoint**
1. **Priority Stations**: Work special event stations or rare DX out of order
2. **Band Changes**: When a station calls on a different band/mode
3. **Logging Software Integration**: Your app detects a QSO starting with a queued station
4. **Manual Selection**: Operator chooses to work a specific station from the visual queue
5. **Emergency/Priority Traffic**: Handle emergency communications immediately

### **Typical Workflow**
1. Your app monitors the queue via `queue_update` broadcasts
2. User selects a specific callsign from the queue display
3. Your app sends `admin_work_specific` request
4. Pileup Buster removes callsign from queue and sets as current QSO
5. All connected clients receive `qso_update` and `queue_update` broadcasts

---

## 📨 **Message Protocol**

### **Request Message**

**Message Type**: `admin_work_specific`

**Required Fields**:
- `type`: Must be "admin_work_specific"
- `request_id`: Unique identifier for request correlation
- `session_token`: Valid admin authentication token
- `callsign`: The callsign to work from the queue

**Request Format**:
```json
{
  "type": "admin_work_specific",
  "request_id": "work_specific_001",
  "session_token": "your_valid_session_token",
  "callsign": "JA1XYZ"
}
```

### **Success Response - Taken from Queue**

When the callsign is successfully removed from the queue and set as current QSO:

```json
{
  "type": "success",
  "request_id": "work_specific_001",
  "message": "Now working JA1XYZ (taken from queue)",
  "data": {
    "current_qso": {
      "callsign": "JA1XYZ",
      "timestamp": "2025-07-24T14:30:00Z",
      "qrz": {
        "name": "Takeshi Yamamoto",
        "address": "Tokyo, Japan", 
        "dxcc_name": "Japan",
        "country": "Japan"
      },
      "metadata": {
        "source": "queue_specific",
        "bridge_initiated": false,
        "original_position": 3
      }
    }
  }
}
```

### **Success Response - Already Current QSO**

When the requested callsign is already the current QSO (graceful handling):

```json
{
  "type": "success",
  "request_id": "work_specific_001", 
  "message": "Already working JA1XYZ (current QSO)",
  "data": {
    "current_qso": {
      "callsign": "JA1XYZ",
      "timestamp": "2025-07-24T14:25:00Z",
      "qrz": {
        "name": "Takeshi Yamamoto",
        "address": "Tokyo, Japan",
        "dxcc_name": "Japan",
        "country": "Japan"
      },
      "metadata": {
        "source": "queue_next",
        "bridge_initiated": false
      }
    }
  }
}
```

### **Error Response**

When the callsign is not found in queue or current QSO:

```json
{
  "type": "error",
  "request_id": "work_specific_001",
  "error_code": "INVALID_REQUEST", 
  "message": "Callsign JA1XYZ not found in queue or current QSO"
}
```

---

## 📡 **Broadcast Messages**

After a successful `admin_work_specific` operation, all connected clients will receive these broadcast messages:

### **QSO Update Broadcast**

Sent when the current QSO changes:

```json
{
  "type": "qso_update",
  "timestamp": "2025-07-24T14:30:00Z",
  "data": {
    "callsign": "JA1XYZ",
    "qrz": {
      "name": "Takeshi Yamamoto", 
      "address": "Tokyo, Japan",
      "dxcc_name": "Japan"
    },
    "started_at": "2025-07-24T14:30:00Z",
    "source": "queue_specific",
    "change_type": "qso_started"
  }
}
```

### **Queue Update Broadcast**

Sent when the queue changes (callsign removed):

```json
{
  "type": "queue_update",
  "timestamp": "2025-07-24T14:30:00Z",
  "data": {
    "queue": [
      {
        "callsign": "DL1ABC", 
        "timestamp": "2025-07-24T14:20:00Z",
        "qrz": {
          "name": "Hans Mueller",
          "address": "Berlin, Germany",
          "dxcc_name": "Germany"
        }
      },
      {
        "callsign": "VK2DEF",
        "timestamp": "2025-07-24T14:22:00Z", 
        "qrz": {
          "name": "Peter Smith",
          "address": "Sydney, Australia",
          "dxcc_name": "Australia"
        }
      }
    ],
    "total": 2,
    "max_size": 4,
    "change_type": "user_worked_specific",
    "affected_callsign": "JA1XYZ"
  }
}
```

---

## 💻 **Implementation Examples**

### **Qt6/C++ Implementation**

```cpp
class PileupBusterClient : public QObject {
    Q_OBJECT

public slots:
    void workSpecificCallsign(const QString& callsign) {
        if (sessionToken.isEmpty()) {
            qDebug() << "Error: Not authenticated";
            return;
        }
        
        QJsonObject request;
        request["type"] = "admin_work_specific";
        request["request_id"] = QString("work_specific_%1").arg(QDateTime::currentMSecsSinceEpoch());
        request["session_token"] = sessionToken;
        request["callsign"] = callsign;
        
        sendMessage(request);
        
        qDebug() << "Requesting to work specific callsign:" << callsign;
    }

    void onMessageReceived(const QString& message) {
        QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
        QJsonObject obj = doc.object();
        
        QString type = obj["type"].toString();
        QString requestId = obj["request_id"].toString();
        
        if (type == "success") {
            QString responseMessage = obj["message"].toString();
            QJsonObject data = obj["data"].toObject();
            QJsonObject currentQso = data["current_qso"].toObject();
            QString callsign = currentQso["callsign"].toString();
            
            if (responseMessage.contains("taken from queue")) {
                qDebug() << "Successfully working" << callsign << "from queue";
                emit callsignWorkedFromQueue(callsign);
            } else if (responseMessage.contains("Already working")) {
                qDebug() << "Callsign" << callsign << "is already current QSO";
                emit callsignAlreadyCurrent(callsign);
            }
            
            // Update UI with current QSO information
            updateCurrentQSODisplay(currentQso);
        }
        else if (type == "error") {
            QString errorCode = obj["error_code"].toString();
            QString errorMessage = obj["message"].toString();
            
            if (errorCode == "INVALID_REQUEST") {
                qDebug() << "Callsign not found in queue or current QSO:" << errorMessage;
                emit callsignNotFound(errorMessage);
            } else {
                qDebug() << "Error working specific callsign:" << errorCode << errorMessage;
                emit operationError(errorCode, errorMessage);
            }
        }
        else if (type == "qso_update") {
            handleQSOUpdateBroadcast(obj["data"].toObject());
        }
        else if (type == "queue_update") {
            handleQueueUpdateBroadcast(obj["data"].toObject());
        }
    }

private:
    void updateCurrentQSODisplay(const QJsonObject& qsoData) {
        QString callsign = qsoData["callsign"].toString();
        QString timestamp = qsoData["timestamp"].toString();
        QJsonObject qrz = qsoData["qrz"].toObject();
        QString name = qrz["name"].toString();
        QString address = qrz["address"].toString();
        QString dxcc = qrz["dxcc_name"].toString();
        
        // Update your UI components
        ui->currentCallsignLabel->setText(callsign);
        ui->currentNameLabel->setText(name);
        ui->currentLocationLabel->setText(address);
        ui->currentCountryLabel->setText(dxcc);
        
        // Get metadata for additional context
        QJsonObject metadata = qsoData["metadata"].toObject();
        QString source = metadata["source"].toString();
        int originalPosition = metadata["original_position"].toInt();
        
        if (source == "queue_specific" && originalPosition > 0) {
            ui->statusLabel->setText(QString("Working %1 (was position %2 in queue)")
                                    .arg(callsign).arg(originalPosition));
        } else {
            ui->statusLabel->setText(QString("Working %1").arg(callsign));
        }
    }
    
    void handleQSOUpdateBroadcast(const QJsonObject& data) {
        QString changeType = data["change_type"].toString();
        QString callsign = data["callsign"].toString();
        
        if (changeType == "qso_started") {
            emit qsoStarted(callsign);
            qDebug() << "QSO started with:" << callsign;
        }
    }
    
    void handleQueueUpdateBroadcast(const QJsonObject& data) {
        QString changeType = data["change_type"].toString();
        QString affectedCallsign = data["affected_callsign"].toString();
        int totalQueue = data["total"].toInt();
        
        if (changeType == "user_worked_specific") {
            emit callsignRemovedFromQueue(affectedCallsign);
            qDebug() << "Callsign" << affectedCallsign << "removed from queue, new size:" << totalQueue;
        }
        
        // Update queue display
        updateQueueDisplay(data["queue"].toArray());
    }

signals:
    void callsignWorkedFromQueue(const QString& callsign);
    void callsignAlreadyCurrent(const QString& callsign);
    void callsignNotFound(const QString& message);
    void operationError(const QString& errorCode, const QString& message);
    void qsoStarted(const QString& callsign);
    void callsignRemovedFromQueue(const QString& callsign);
};
```

### **Python Implementation**

```python
import asyncio
import websockets
import json
import time
from typing import Dict, Any, Callable, Optional

class PileupBusterClient:
    def __init__(self):
        self.websocket = None
        self.session_token = None
        self.response_handlers = {}
        self.broadcast_handlers = {
            'qso_update': self.handle_qso_update,
            'queue_update': self.handle_queue_update
        }
        
    async def work_specific_callsign(self, callsign: str) -> Dict[str, Any]:
        """
        Work a specific callsign from the queue
        
        Args:
            callsign: The callsign to work from the queue
            
        Returns:
            Response dictionary with operation result
        """
        if not self.session_token:
            raise ValueError("Not authenticated - call authenticate() first")
            
        request = {
            "type": "admin_work_specific",
            "request_id": f"work_specific_{int(time.time() * 1000)}",
            "session_token": self.session_token,
            "callsign": callsign
        }
        
        print(f"Requesting to work specific callsign: {callsign}")
        response = await self.send_and_wait_response(request)
        
        if response.get("type") == "success":
            message = response.get("message", "")
            data = response.get("data", {})
            current_qso = data.get("current_qso", {})
            
            if "taken from queue" in message:
                print(f"✅ Successfully working {callsign} from queue")
                self.on_callsign_worked_from_queue(current_qso)
            elif "Already working" in message:
                print(f"ℹ️ Callsign {callsign} is already current QSO")
                self.on_callsign_already_current(current_qso)
                
        elif response.get("type") == "error":
            error_code = response.get("error_code")
            error_message = response.get("message")
            
            if error_code == "INVALID_REQUEST":
                print(f"❌ Callsign not found: {error_message}")
            else:
                print(f"❌ Error: {error_code} - {error_message}")
                
        return response
        
    def on_callsign_worked_from_queue(self, qso_data: Dict[str, Any]):
        """Handle successful callsign worked from queue"""
        callsign = qso_data.get("callsign")
        qrz = qso_data.get("qrz", {})
        name = qrz.get("name", "")
        location = qrz.get("address", "")
        country = qrz.get("dxcc_name", "")
        
        metadata = qso_data.get("metadata", {})
        original_position = metadata.get("original_position", 0)
        
        print(f"📻 Now working: {callsign}")
        print(f"   Name: {name}")
        print(f"   Location: {location}")
        print(f"   Country: {country}")
        if original_position > 0:
            print(f"   Was position {original_position} in queue")
            
        # Update your application's UI/state here
        self.update_current_qso_display(qso_data)
        
    def on_callsign_already_current(self, qso_data: Dict[str, Any]):
        """Handle case where callsign is already current QSO"""
        callsign = qso_data.get("callsign")
        print(f"ℹ️ {callsign} is already the current QSO - no change needed")
        
        # Your app might want to highlight this in the UI
        self.highlight_current_qso_unchanged(qso_data)
        
    async def handle_qso_update(self, data: Dict[str, Any]):
        """Handle QSO update broadcasts"""
        qso_data = data.get("data", {})
        change_type = qso_data.get("change_type")
        callsign = qso_data.get("callsign")
        
        if change_type == "qso_started":
            print(f"🔔 Broadcast: QSO started with {callsign}")
            self.update_current_qso_display(qso_data)
            
    async def handle_queue_update(self, data: Dict[str, Any]):
        """Handle queue update broadcasts"""
        queue_data = data.get("data", {})
        change_type = queue_data.get("change_type")
        affected_callsign = queue_data.get("affected_callsign")
        total = queue_data.get("total", 0)
        
        if change_type == "user_worked_specific":
            print(f"🔔 Broadcast: {affected_callsign} removed from queue (worked specifically)")
            print(f"   New queue size: {total}")
            
        # Update queue display in your app
        queue = queue_data.get("queue", [])
        self.update_queue_display(queue)
        
    def update_current_qso_display(self, qso_data: Dict[str, Any]):
        """Update your application's current QSO display"""
        # Implement this method to update your UI
        pass
        
    def highlight_current_qso_unchanged(self, qso_data: Dict[str, Any]):
        """Highlight that current QSO didn't change"""
        # Implement this method to show user the QSO was already current
        pass
        
    def update_queue_display(self, queue: list):
        """Update your application's queue display"""
        # Implement this method to update your queue UI
        pass

# Usage Example
async def example_usage():
    client = PileupBusterClient()
    
    # Connect and authenticate
    await client.connect()
    await client.authenticate("admin", "your_password")
    
    # Work a specific callsign from queue
    result = await client.work_specific_callsign("JA1XYZ")
    
    # Handle the result
    if result.get("type") == "success":
        print("Operation successful!")
    else:
        print(f"Operation failed: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())
```

---

## ⚠️ **Error Handling**

### **Common Error Scenarios**

1. **Callsign Not Found**
   - **Error Code**: `INVALID_REQUEST`
   - **Message**: "Callsign XYZ not found in queue or current QSO"
   - **Cause**: The callsign is not in the queue and not the current QSO
   - **Action**: Check queue status, inform user callsign not available

2. **Authentication Required**
   - **Error Code**: `AUTH_REQUIRED` 
   - **Message**: "Valid session token required for admin operations"
   - **Cause**: Missing or invalid session token
   - **Action**: Re-authenticate before retrying

3. **Session Expired**
   - **Error Code**: `SESSION_EXPIRED`
   - **Message**: "Session token has expired"
   - **Cause**: Token older than 24 hours
   - **Action**: Re-authenticate with credentials

### **Robust Error Handling Example**

```cpp
void PileupBusterClient::workSpecificCallsignWithRetry(const QString& callsign) {
    if (sessionToken.isEmpty()) {
        // Attempt re-authentication first
        authenticate(storedUsername, storedPassword);
        
        // Queue the request for after authentication
        pendingRequests.enqueue(callsign);
        return;
    }
    
    QJsonObject request;
    request["type"] = "admin_work_specific";
    request["request_id"] = QString("work_specific_%1").arg(QDateTime::currentMSecsSinceEpoch());
    request["session_token"] = sessionToken;
    request["callsign"] = callsign;
    
    // Store retry information
    RequestRetryInfo retryInfo;
    retryInfo.originalRequest = request;
    retryInfo.retryCount = 0;
    retryInfo.maxRetries = 3;
    
    retryMap[request["request_id"].toString()] = retryInfo;
    
    sendMessage(request);
}

void PileupBusterClient::handleErrorResponse(const QJsonObject& error) {
    QString requestId = error["request_id"].toString();
    QString errorCode = error["error_code"].toString();
    QString errorMessage = error["message"].toString();
    
    if (errorCode == "AUTH_REQUIRED" || errorCode == "SESSION_EXPIRED") {
        // Handle authentication errors
        qDebug() << "Authentication error, re-authenticating...";
        sessionToken.clear();
        
        if (retryMap.contains(requestId)) {
            RequestRetryInfo retryInfo = retryMap[requestId];
            if (retryInfo.retryCount < retryInfo.maxRetries) {
                // Re-authenticate and retry
                authenticate(storedUsername, storedPassword);
                retryAfterAuth.append(retryInfo.originalRequest);
            } else {
                emit operationFailed("Authentication failed after retries");
            }
            retryMap.remove(requestId);
        }
    } 
    else if (errorCode == "INVALID_REQUEST") {
        // Handle callsign not found
        QString callsign = extractCallsignFromRequest(requestId);
        emit callsignNotFound(callsign, errorMessage);
        retryMap.remove(requestId);
    }
    else {
        // Handle other errors
        emit operationError(errorCode, errorMessage);
        retryMap.remove(requestId);
    }
}
```

---

## 🎯 **Best Practices**

### **For Your Application**

1. **Queue Monitoring**: Always monitor `queue_update` broadcasts to maintain accurate queue state
2. **Graceful Degradation**: Handle "already current QSO" responses gracefully 
3. **User Feedback**: Provide clear feedback about operation results
4. **Error Recovery**: Implement automatic retry for authentication errors
5. **UI Updates**: Update displays immediately based on broadcast messages

### **Message Correlation**

```cpp
// Always use unique request IDs
QString generateRequestId(const QString& prefix) {
    return QString("%1_%2_%3")
        .arg(prefix)
        .arg(QDateTime::currentMSecsSinceEpoch())
        .arg(QRandomGenerator::global()->bounded(1000, 9999));
}

// Store pending requests for timeout handling
void sendRequestWithTimeout(const QJsonObject& request, int timeoutMs = 10000) {
    QString requestId = request["request_id"].toString();
    
    PendingRequest pending;
    pending.request = request;
    pending.timestamp = QDateTime::currentDateTime();
    pending.timeoutMs = timeoutMs;
    
    pendingRequests[requestId] = pending;
    
    // Set timeout timer
    QTimer::singleShot(timeoutMs, [this, requestId]() {
        if (pendingRequests.contains(requestId)) {
            emit requestTimedOut(requestId);
            pendingRequests.remove(requestId);
        }
    });
    
    sendMessage(request);
}
```

### **UI Integration Tips**

1. **Visual Feedback**: Show loading states while requests are pending
2. **Queue Highlighting**: Highlight callsigns that can be worked specifically
3. **Context Menus**: Add "Work Now" options to queue entries
4. **Status Display**: Show whether current QSO came from queue or direct entry
5. **Position Tracking**: Display original queue positions in QSO history

---

## 🔍 **Testing Your Integration**

### **Manual Testing Steps**

1. **Setup Test Environment**:
   ```bash
   # Start Pileup Buster backend
   cd backend
   poetry run start
   ```

2. **Register Test Callsigns**:
   - Add several callsigns to queue using web interface or API
   - Verify queue contains multiple stations

3. **Test Work Specific**:
   - Use your app to work a callsign from middle of queue
   - Verify callsign becomes current QSO
   - Verify callsign removed from queue
   - Check broadcast messages received

4. **Test Already Current**:
   - Try to work the same callsign again
   - Verify graceful response received
   - Confirm no state changes

5. **Test Error Cases**:
   - Try to work non-existent callsign
   - Test with invalid authentication
   - Verify proper error handling

### **Automated Testing Example**

```python
async def test_work_specific_integration():
    client = PileupBusterClient()
    
    # Setup
    await client.connect()
    await client.authenticate("admin", "password")
    
    # Add test callsigns to queue
    await client.register_callsign("EA1ABC")
    await client.register_callsign("JA1XYZ") 
    await client.register_callsign("DL1DEF")
    
    # Test working specific callsign
    result = await client.work_specific_callsign("JA1XYZ")
    assert result["type"] == "success"
    assert "taken from queue" in result["message"]
    
    # Test working already current QSO
    result2 = await client.work_specific_callsign("JA1XYZ")
    assert result2["type"] == "success"
    assert "Already working" in result2["message"]
    
    # Test non-existent callsign
    result3 = await client.work_specific_callsign("XX9XXX")
    assert result3["type"] == "error"
    assert result3["error_code"] == "INVALID_REQUEST"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_work_specific_integration())
```

---

## 📚 **Related Documentation**

- **[Complete WebSocket API Reference](WS-All.prd)**: Full API documentation
- **[WebSocket Authentication Guide](docs/WEBSOCKET_API_DOCUMENTATION.md)**: Authentication details
- **[Qt6 Integration Guide](QT6_WEBSOCKET_IMPLEMENTATION_GUIDE.md)**: C++/Qt6 examples
- **[Real-time Events Documentation](WS-All.prd#real-time-events--broadcasting)**: Broadcast message details

---

## 🆘 **Support**

If you encounter issues implementing this endpoint:

1. **Check Authentication**: Ensure session token is valid and not expired
2. **Verify Queue State**: Confirm callsign exists in queue before working
3. **Monitor Broadcasts**: Watch for `qso_update` and `queue_update` messages
4. **Test Error Handling**: Implement robust error handling for all scenarios
5. **Review Logs**: Check backend logs for detailed error information

For additional support, create an issue in the repository with:
- Your implementation code
- Error messages received
- Expected vs actual behavior
- WebSocket message traces

---

**Document End** - Last Updated: July 24, 2025
