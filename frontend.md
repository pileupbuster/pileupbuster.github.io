# Frontend SSE Integration Guide

This guide explains how the Pileup Buster frontend uses Server-Sent Events (SSE) for real-time communication with the backend, and how these patterns can be applied to other applications like QT6/C++ logging software.

## SSE Architecture Overview

### Connection Model
The frontend establishes a **single persistent SSE connection** to the backend's `/api/events/stream` endpoint. This connection:

- **Stays alive continuously** during the application lifecycle
- **Auto-reconnects** with exponential backoff when disconnected
- **Receives multiple event types** on the same connection
- **Provides fallback polling** if SSE fails

### Event-Driven State Management
The frontend uses SSE events as the **primary source of truth** for state updates, not direct API responses. This means:

- API calls trigger changes on the backend
- Backend broadcasts events to all connected clients
- Frontend updates its state based on received events
- Multiple clients stay synchronized automatically

## Core SSE Service Patterns

### 1. Connection Management

**Connection Lifecycle:**
```
1. Initialize EventSource with endpoint URL
2. Register event listeners for each event type
3. Handle connection opened (reset reconnection state)
4. Handle connection errors (trigger reconnection)
5. Implement exponential backoff for reconnections
6. Clean up on application exit
```

**Key Connection Features:**
- **Connection State Tracking**: Monitor `EventSource.readyState` (CONNECTING=0, OPEN=1, CLOSED=2)
- **Reconnection Logic**: Automatic retry with increasing delays (1s, 2s, 4s, 8s, up to 30s)
- **Connection Health**: Backend sends `keepalive` events every 30 seconds
- **Initial Confirmation**: Backend sends `connected` event on successful connection

### 2. Event Type Registration

The frontend registers handlers for specific event types:

**Event Types Handled:**
- `connected` - Initial connection confirmation
- `keepalive` - Connection health monitoring (every 30s)
- `current_qso` - Active QSO state changes
- `queue_update` - Queue list modifications
- `system_status` - System active/inactive state
- `frequency_update` - Frequency changes
- `split_update` - Split frequency changes

**Pattern:** Each event type has dedicated handlers that update specific parts of the application state.

### 3. Event Data Structure

All events follow a consistent structure:
```json
{
  "type": "event_name",
  "data": { /* event-specific payload */ },
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

**Event Processing Pattern:**
1. Parse JSON event data
2. Extract event-specific payload from `data` field
3. Update relevant application state
4. Handle errors gracefully (log but don't crash)

## Callsign Registration Flow

### User Action Triggers Event Chain

**1. User Registration:**
```
Frontend: POST /api/queue/register {"callsign": "KC1ABC"}
   ↓
Backend: Validates callsign → Looks up QRZ data → Stores in database
   ↓
Backend: Broadcasts "queue_update" event to ALL connected clients
   ↓
Frontend: Receives event → Updates queue display
```

**2. Event Content:**
The `queue_update` event contains:
```json
{
  "type": "queue_update",
  "data": {
    "queue": [
      {
        "callsign": "KC1ABC",
        "timestamp": "2025-01-01T12:00:00Z",
        "position": 1,
        "qrz": {
          "name": "John Doe",
          "address": "123 Main St, City, State",
          "image": "http://qrz.com/image.jpg"
        }
      }
    ],
    "total": 1,
    "max_size": 4,
    "system_active": true
  }
}
```

**3. Frontend Response:**
- Updates queue list display immediately
- Shows new queue count
- No manual refresh needed
- All connected clients see the same update

## Connection Keep-Alive Strategy

### Multi-Layer Approach

**1. SSE-Level Keep-Alive:**
- Backend sends `keepalive` events every 30 seconds
- Frontend logs these but doesn't process them as UI updates
- Prevents browser/proxy from closing idle connections

**2. Application-Level Fallback:**
- Frontend polls every 30 seconds IF SSE is disconnected
- Fallback fetches current QSO and queue data via REST API
- Ensures functionality even if SSE completely fails

**3. Reconnection Strategy:**
- Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (max)
- Adds random jitter to prevent thundering herd
- Maximum 5 reconnection attempts before giving up
- Resets retry count on successful connection

### Connection Health Monitoring

**Frontend Checks:**
```cpp
// Equivalent logic for QT6:
bool isConnected = (eventSource->readyState() == QNetworkReply::Finished);
if (!isConnected) {
    // Use fallback polling
    pollCurrentQso();
    pollQueueList();
}
```

## State Synchronization Patterns

### 1. Immediate Local Updates + Event Confirmation

**Pattern:** Optimistic updates with SSE confirmation

```
User clicks "Set Frequency" → 
Frontend immediately updates display → 
POST /api/admin/frequency → 
Backend broadcasts "frequency_update" → 
Frontend receives event (confirms success)
```

**Why:** Provides immediate UI feedback while ensuring consistency across all clients.

### 2. Event-Only Updates (No Immediate Changes)

**Pattern:** Wait for SSE event to update state

```
User registers callsign → 
POST /api/queue/register → 
Wait for "queue_update" event → 
Update queue display
```

**Why:** Queue changes affect multiple clients, so waiting for the broadcast ensures everyone sees the same state.

## Error Handling and Resilience

### Connection Error Recovery

**1. Network Interruption:**
- SSE connection drops
- Frontend detects via `onerror` event
- Automatic reconnection with backoff
- Fallback polling during disconnection

**2. Server Restart:**
- All SSE connections lost
- Clients automatically reconnect
- Backend sends `connected` event
- Frontend refetches initial state on reconnection

**3. Malformed Events:**
- Individual event parsing fails
- Error logged but application continues
- Other events continue to process normally

### Graceful Degradation

**When SSE Fails:**
1. Fall back to 30-second REST API polling
2. Core functionality remains available
3. Real-time updates become periodic updates
4. User experience degrades gracefully

## Implementation Guidelines for QT6/C++

### 1. SSE Connection Setup

```cpp
// Create QNetworkAccessManager for SSE
QNetworkAccessManager* manager = new QNetworkAccessManager(this);

// Create SSE request
QNetworkRequest request(QUrl("http://localhost:8000/api/events/stream"));
request.setRawHeader("Accept", "text/event-stream");
request.setRawHeader("Cache-Control", "no-cache");

// Start the connection
QNetworkReply* reply = manager->get(request);

// Handle incoming data
connect(reply, &QNetworkReply::readyRead, [=]() {
    QByteArray data = reply->readAll();
    parseSSEData(data);
});
```

### 2. Event Parsing Pattern

```cpp
void parseSSEData(const QByteArray& data) {
    QString content = QString::fromUtf8(data);
    QStringList lines = content.split("\n");
    
    QString eventType;
    QString eventData;
    
    for (const QString& line : lines) {
        if (line.startsWith("event:")) {
            eventType = line.mid(6).trimmed();
        } else if (line.startsWith("data:")) {
            eventData = line.mid(5).trimmed();
        } else if (line.isEmpty() && !eventType.isEmpty()) {
            // Process complete event
            handleEvent(eventType, eventData);
            eventType.clear();
            eventData.clear();
        }
    }
}
```

### 3. Event Handler Registration

```cpp
void handleEvent(const QString& eventType, const QString& jsonData) {
    QJsonDocument doc = QJsonDocument::fromJson(jsonData.toUtf8());
    QJsonObject eventObj = doc.object();
    QJsonObject data = eventObj["data"].toObject();
    
    if (eventType == "connected") {
        handleConnected(data);
    } else if (eventType == "queue_update") {
        handleQueueUpdate(data);
    } else if (eventType == "current_qso") {
        handleCurrentQsoUpdate(data);
    } else if (eventType == "frequency_update") {
        handleFrequencyUpdate(data);
    }
    // etc.
}
```

### 4. Reconnection Implementation

```cpp
class SSEClient : public QObject {
private:
    QTimer* reconnectTimer;
    int reconnectAttempts = 0;
    int reconnectDelay = 1000; // Start with 1 second
    
    void handleConnectionError() {
        if (reconnectAttempts >= 5) {
            // Give up and use fallback polling
            startFallbackPolling();
            return;
        }
        
        reconnectAttempts++;
        
        // Exponential backoff with jitter
        int delay = reconnectDelay + (qrand() % 1000);
        reconnectTimer->setSingleShot(true);
        reconnectTimer->start(delay);
        
        // Double the delay for next time (max 30 seconds)
        reconnectDelay = qMin(reconnectDelay * 2, 30000);
    }
    
    void onReconnectTimer() {
        connectToSSE();
    }
};
```

### 5. Fallback Polling Strategy

```cpp
void startFallbackPolling() {
    QTimer* pollTimer = new QTimer(this);
    connect(pollTimer, &QTimer::timeout, [=]() {
        if (!isSSEConnected()) {
            // Poll critical endpoints
            fetchCurrentQso();
            fetchQueueList();
            fetchSystemStatus();
        }
    });
    pollTimer->start(30000); // 30 seconds
}
```

## Testing Your SSE Integration

### 1. Connection Verification

**Test Steps:**
1. Connect to `/api/events/stream`
2. Verify `connected` event received immediately
3. Wait for `keepalive` events every 30 seconds
4. Monitor connection state continuously

### 2. Event Flow Testing

**Registration Test:**
1. POST to `/api/queue/register` with test callsign
2. Verify `queue_update` event received
3. Check event data contains new callsign
4. Confirm queue count incremented

**QSO Management Test:**
1. Use admin API to start QSO with next callsign
2. Verify `current_qso` event received
3. Verify `queue_update` event (callsign removed from queue)
4. Confirm UI updates correctly

### 3. Resilience Testing

**Network Interruption:**
1. Disconnect network briefly
2. Verify automatic reconnection occurs
3. Check fallback polling activates
4. Confirm state synchronizes after reconnection

## Best Practices Summary

### 1. Connection Management
- Use single persistent connection for all event types
- Implement exponential backoff reconnection
- Provide fallback polling for critical functionality
- Clean up connections properly on exit

### 2. Event Processing
- Parse events safely with error handling
- Update UI state only from events, not API responses
- Log events for debugging but don't overwhelm logs
- Handle malformed events gracefully

### 3. State Synchronization
- Use events as source of truth for shared state
- Implement optimistic updates only for immediate UI feedback
- Refetch initial state on reconnection
- Handle concurrent modifications properly

### 4. User Experience
- Show connection status to users
- Provide graceful degradation when SSE fails
- Maintain responsive UI during connection issues
- Cache critical data for offline viewing

This architecture ensures robust real-time synchronization between your logging software and the Pileup Buster system, with automatic recovery from network issues and consistent state across all connected clients.
