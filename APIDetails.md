# Pileup Buster API Documentation

## Overview

This document provides comprehensive API documentation for integrating logging software with Pileup Buster. The API supports both RESTful HTTP endpoints and real-time Server-Sent Events (SSE) for efficient bidirectional communication.

**Base URL:** `http://localhost:8000`  
**Protocol:** HTTP/HTTPS  
**Authentication:** Basic Auth for admin endpoints only  
**Real-time:** Server-Sent Events on `/api/events/stream`

## Authentication

### Admin Endpoints
Some endpoints require HTTP Basic Authentication:
- **Username:** Configure via `ADMIN_USERNAME` environment variable
- **Password:** Configure via `ADMIN_PASSWORD` environment variable
- **Header:** `Authorization: Basic <base64(username:password)>`

### Public Endpoints
Most monitoring and queue endpoints are public and require no authentication.

## Server-Sent Events (SSE)

### Connection Endpoint
**URL:** `GET /api/events/stream`  
**Headers:** 
```
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### SSE Event Format
```
event: event_name
data: {"type": "event_name", "data": {...}, "timestamp": "2025-07-16T14:30:45.123Z"}

```

### Event Types

#### 1. Connection Established
**Event:** `connected`
```json
{
  "type": "connected",
  "data": {
    "message": "SSE connection established",
    "server_time": "2025-07-16T14:30:45.123Z"
  },
  "timestamp": "2025-07-16T14:30:45.123Z"
}
```

#### 2. Current QSO Updates
**Event:** `current_qso`
```json
{
  "type": "current_qso",
  "data": {
    "callsign": "EI6LF",
    "timestamp": "2025-07-16T14:30:45Z",
    "qrz": {
      "callsign": "EI6LF",
      "name": "John Smith",
      "address": "Dublin, Ireland",
      "dxcc_name": "Ireland",
      "image": "https://www.qrz.com/db/EI6LF?pic",
      "url": "https://www.qrz.com/db/EI6LF"
    },
    "metadata": {
      "frequency_mhz": 14.2715,
      "mode": "SSB",
      "source": "queue",
      "started_via": "logging_software",
      "bridge_initiated": false
    }
  },
  "timestamp": "2025-07-16T14:30:45.123Z"
}
```

**Triggered when:**
- New QSO starts (admin clicks "Next" or logging software sends QSO)
- QSO is cleared/completed (`data` will be `null`)

#### 3. Queue Updates
**Event:** `queue_update`
```json
{
  "type": "queue_update",
  "data": {
    "queue": [
      {
        "callsign": "W1ABC",
        "timestamp": "2025-07-16T14:30:45Z",
        "position": 1,
        "qrz": {
          "callsign": "W1ABC",
          "name": "Jane Wilson",
          "address": "Boston, MA, United States",
          "dxcc_name": "United States",
          "image": "https://www.qrz.com/db/W1ABC?pic"
        }
      }
    ],
    "total": 1,
    "max_size": 4,
    "system_active": true
  },
  "timestamp": "2025-07-16T14:30:45.123Z"
}
```

**Triggered when:**
- New callsign registers in queue
- Callsign is removed from queue
- Queue is cleared
- System status changes

#### 4. System Status Changes
**Event:** `system_status`
```json
{
  "type": "system_status",
  "data": {
    "active": true,
    "last_updated": "2025-07-16T14:30:45Z",
    "updated_by": "admin"
  },
  "timestamp": "2025-07-16T14:30:45.123Z"
}
```

**Triggered when:**
- System is activated/deactivated via admin panel

#### 5. Frequency Updates
**Event:** `frequency_update`
```json
{
  "type": "frequency_update",
  "data": {
    "frequency": "14.205 MHz",
    "last_updated": "2025-07-16T14:30:45Z",
    "updated_by": "admin"
  },
  "timestamp": "2025-07-16T14:30:45.123Z"
}
```

**Triggered when:**
- Operating frequency is set/cleared via admin panel

#### 6. Keepalive Events
**Event:** `keepalive`
```json
{
  "type": "keepalive",
  "data": {},
  "timestamp": "2025-07-16T14:30:45.123Z"
}
```

**Purpose:** Sent every 30 seconds to maintain SSE connection

## REST API Endpoints

### Public Endpoints (No Authentication Required)

#### Get System Status
**URL:** `GET /api/queue/status`  
**Purpose:** Check if system is active and accepting registrations

**Response:**
```json
{
  "active": true,
  "last_updated": "2025-07-16T14:30:45Z"
}
```

#### Get Current QSO
**URL:** `GET /api/queue/current`  
**Purpose:** Get currently active QSO or null if none

**Response (Active QSO):**
```json
{
  "callsign": "EI6LF",
  "timestamp": "2025-07-16T14:30:45Z",
  "qrz": {
    "callsign": "EI6LF",
    "name": "John Smith",
    "address": "Dublin, Ireland",
    "dxcc_name": "Ireland",
    "image": "https://www.qrz.com/db/EI6LF?pic",
    "url": "https://www.qrz.com/db/EI6LF"
  },
  "metadata": {
    "frequency_mhz": 14.2715,
    "mode": "SSB",
    "source": "queue",
    "started_via": "logging_software"
  }
}
```

**Response (No Active QSO):**
```json
null
```

#### Get Queue List
**URL:** `GET /api/queue/list`  
**Purpose:** Get all waiting callsigns in FIFO order

**Response:**
```json
{
  "queue": [
    {
      "callsign": "W1ABC",
      "timestamp": "2025-07-16T14:30:45Z",
      "position": 1,
      "qrz": {
        "callsign": "W1ABC",
        "name": "Jane Wilson",
        "address": "Boston, MA, United States",
        "dxcc_name": "United States",
        "image": "https://www.qrz.com/db/W1ABC?pic"
      }
    },
    {
      "callsign": "VK2DEF",
      "timestamp": "2025-07-16T14:31:12Z",
      "position": 2,
      "qrz": {
        "callsign": "VK2DEF",
        "name": "Bob Johnson",
        "address": "Sydney, NSW, Australia",
        "dxcc_name": "Australia"
      }
    }
  ],
  "total": 2,
  "max_size": 4,
  "system_active": true
}
```

#### Get Current Frequency
**URL:** `GET /api/public/frequency`  
**Purpose:** Get current operating frequency

**Response:**
```json
{
  "frequency": "14.205 MHz",
  "last_updated": "2025-07-16T14:30:45Z"
}
```

**Response (No Frequency Set):**
```json
{
  "frequency": null
}
```

#### Register Callsign in Queue
**URL:** `POST /api/queue/register`  
**Headers:** `Content-Type: application/json`  
**Purpose:** Add callsign to waiting queue

**Request:**
```json
{
  "callsign": "EI6LF"
}
```

**Response (Success):**
```json
{
  "message": "Callsign registered successfully",
  "entry": {
    "callsign": "EI6LF",
    "timestamp": "2025-07-16T14:30:45Z",
    "position": 3,
    "qrz": {
      "callsign": "EI6LF",
      "name": "John Smith",
      "address": "Dublin, Ireland",
      "dxcc_name": "Ireland"
    }
  }
}
```

**Error Responses:**
- **HTTP 400:** Invalid callsign format
- **HTTP 409:** Callsign already in queue
- **HTTP 503:** System inactive
- **HTTP 507:** Queue full

#### Remove Callsign from Queue
**URL:** `DELETE /api/queue/remove/{callsign}`  
**Purpose:** Remove specific callsign from queue

**Response:**
```json
{
  "message": "Callsign EI6LF removed from queue",
  "removed_entry": {
    "callsign": "EI6LF",
    "position": 2
  }
}
```

**Error Responses:**
- **HTTP 404:** Callsign not found in queue
- **HTTP 503:** System inactive

### Admin Endpoints (Authentication Required)

#### Send QSO from Logging Software
**URL:** `POST /api/admin/qso/logging-direct`  
**Headers:** `Content-Type: application/json`  
**Authentication:** None required  
**Purpose:** Notify Pileup Buster of QSO start from logging software

**Request:**
```json
{
  "type": "qso_start",
  "data": {
    "callsign": "EI6LF",
    "frequency_mhz": 14.2715,
    "mode": "SSB",
    "source": "pblog_native",
    "timestamp": "2025-07-16T14:30:45.000Z",
    "triggered_by": "callsign_finalized"
  }
}
```

**Response:**
```json
{
  "type": "ack",
  "timestamp": "2025-07-16T14:30:45.123Z",
  "received": {
    "type": "qso_start",
    "data": {
      "callsign": "EI6LF",
      "frequency_mhz": 14.2715,
      "mode": "SSB",
      "source": "pblog_native",
      "timestamp": "2025-07-16T14:30:45.000Z",
      "triggered_by": "callsign_finalized"
    }
  },
  "qso_started": {
    "callsign": "EI6LF",
    "source": "direct",
    "was_in_queue": false,
    "frequency_mhz": 14.2715,
    "mode": "SSB"
  }
}
```

**Error Responses:**
- **HTTP 400:** Invalid message format
- **HTTP 503:** System inactive or logger integration disabled

#### Get/Set System Status
**URL:** `GET /api/admin/status`  
**Authentication:** Required

**Response:**
```json
{
  "active": true,
  "last_updated": "2025-07-16T14:30:45Z",
  "updated_by": "admin"
}
```

**URL:** `POST /api/admin/status`  
**Authentication:** Required  
**Headers:** `Content-Type: application/json`

**Request:**
```json
{
  "active": true
}
```

**Response:**
```json
{
  "message": "System activated successfully. Queue cleared (0 entries removed). Current QSO cleared",
  "status": {
    "active": true,
    "last_updated": "2025-07-16T14:30:45Z",
    "updated_by": "admin"
  }
}
```

#### Process Next QSO from Queue
**URL:** `POST /api/admin/queue/next`  
**Authentication:** Required  
**Purpose:** Move next person from queue to current QSO

**Response:**
```json
{
  "callsign": "EI6LF",
  "timestamp": "2025-07-16T14:30:45Z",
  "qrz": {
    "callsign": "EI6LF",
    "name": "John Smith",
    "address": "Dublin, Ireland",
    "dxcc_name": "Ireland"
  }
}
```

**Response (Empty Queue):**
```json
null
```

#### Complete Current QSO
**URL:** `POST /api/admin/qso/complete`  
**Authentication:** Required  
**Purpose:** Mark current QSO as complete and clear it

**Response:**
```json
{
  "message": "QSO with EI6LF completed successfully",
  "completed_qso": {
    "callsign": "EI6LF",
    "timestamp": "2025-07-16T14:30:45Z"
  }
}
```

#### Clear Queue
**URL:** `POST /api/admin/queue/clear`  
**Authentication:** Required  
**Purpose:** Remove all entries from queue

**Response:**
```json
{
  "message": "Queue cleared. Removed 3 entries.",
  "cleared_count": 3
}
```

#### Get/Set Operating Frequency
**URL:** `GET /api/admin/frequency`  
**Authentication:** Required

**Response:**
```json
{
  "frequency": "14.205 MHz",
  "last_updated": "2025-07-16T14:30:45Z",
  "updated_by": "admin"
}
```

**URL:** `POST /api/admin/frequency`  
**Authentication:** Required  
**Headers:** `Content-Type: application/json`

**Request:**
```json
{
  "frequency": "14.205 MHz"
}
```

**Response:**
```json
{
  "message": "Frequency set to 14.205 MHz",
  "frequency": "14.205 MHz",
  "last_updated": "2025-07-16T14:30:45Z",
  "updated_by": "admin"
}
```

#### Clear Operating Frequency
**URL:** `DELETE /api/admin/frequency`  
**Authentication:** Required

**Response:**
```json
{
  "message": "Frequency cleared",
  "frequency": null
}
```

#### Get/Set Logger Integration Settings
**URL:** `GET /api/admin/logger-integration`  
**Authentication:** Required

**Response:**
```json
{
  "enabled": true,
  "last_updated": "2025-07-16T14:30:45Z",
  "updated_by": "admin"
}
```

**URL:** `POST /api/admin/logger-integration`  
**Authentication:** Required  
**Headers:** `Content-Type: application/json`

**Request:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "message": "Send to logger enabled successfully",
  "enabled": true,
  "last_updated": "2025-07-16T14:30:45Z",
  "updated_by": "admin"
}
```

#### Get Current QSO (Admin)
**URL:** `GET /api/admin/qso/current`  
**Authentication:** Required  
**Purpose:** Admin version that works regardless of system status

**Response:** Same format as public `/api/queue/current`

## Data Models

### QSO Metadata Fields
- **`source`:** `"queue"` | `"direct"` - Where QSO originated
- **`started_via`:** `"logging_software"` | `"manual"` | `"queue"` - How QSO was initiated
- **`frequency_mhz`:** Number - Operating frequency in MHz
- **`mode`:** String - Operating mode (SSB, CW, FT8, etc.)
- **`bridge_initiated`:** Boolean - Legacy field, usually false

### QRZ Information Fields
- **`callsign`:** String - Ham radio callsign
- **`name`:** String | null - Operator name
- **`address`:** String | null - Full address
- **`dxcc_name`:** String | null - Country/entity name
- **`image`:** String | null - QRZ photo URL
- **`url`:** String | null - QRZ profile URL
- **`error`:** String | null - Error message if lookup failed

### Queue Entry Fields
- **`callsign`:** String - Ham radio callsign
- **`timestamp`:** String - ISO 8601 timestamp when added
- **`position`:** Number - Position in queue (1-based)
- **`qrz`:** Object - QRZ lookup information

## Error Handling

### HTTP Status Codes
- **200:** Success
- **400:** Bad Request - Invalid data format
- **401:** Unauthorized - Invalid admin credentials
- **404:** Not Found - Resource not found
- **409:** Conflict - Duplicate entry
- **503:** Service Unavailable - System inactive
- **507:** Insufficient Storage - Queue full

### SSE Error Handling
- **Connection Lost:** Implement exponential backoff reconnection
- **Parse Errors:** Log and continue processing other events
- **Invalid JSON:** Skip malformed events
- **Network Timeout:** Retry connection after delay

### Recommended Retry Logic
```
Attempt 1: Immediate
Attempt 2: 1 second delay
Attempt 3: 2 second delay
Attempt 4: 4 second delay
Attempt 5: 8 second delay
Attempt 6+: 16 second delay (max)
```

## Implementation Guidelines

### SSE Best Practices
1. **Maintain persistent connection** to `/api/events/stream`
2. **Handle all event types** even if not immediately used
3. **Implement robust reconnection** with exponential backoff
4. **Parse events incrementally** as data arrives
5. **Update UI on main thread** using appropriate threading mechanisms

### HTTP Request Best Practices
1. **Set appropriate timeouts** (10-30 seconds)
2. **Use connection pooling** for multiple requests
3. **Handle network errors gracefully**
4. **Validate JSON responses** before processing
5. **Log errors for debugging** without exposing sensitive data

### Integration Patterns
1. **Primary Communication:** Use SSE for real-time updates
2. **Fallback Polling:** Use REST endpoints if SSE fails
3. **State Synchronization:** Compare local state with API responses
4. **Error Recovery:** Graceful degradation when integration fails
5. **User Feedback:** Show connection status and integration health

### Threading Considerations
- **SSE Connection:** Run on background thread
- **Event Processing:** Parse events on background thread
- **UI Updates:** Send parsed data to main thread for UI updates
- **HTTP Requests:** Use async/await patterns where available

## Security Considerations

### Network Security
- **HTTPS:** Use HTTPS in production deployments
- **Local Only:** Default configuration assumes localhost deployment
- **Firewall:** Only outbound connections required from logging software

### Data Validation
- **Callsign Format:** Validate against ITU standards
- **Frequency Range:** Validate against amateur radio bands
- **JSON Schema:** Validate all incoming JSON data
- **XSS Prevention:** Sanitize all user-provided data

## Performance Optimization

### SSE Performance
- **Single Connection:** Use one SSE connection per application instance
- **Event Batching:** Process multiple events in batches when possible
- **Memory Management:** Clean up event data after processing
- **Connection Reuse:** Reuse HTTP connections for REST requests

### Data Caching
- **Queue State:** Cache current queue state locally
- **QRZ Data:** Cache QRZ lookups to reduce API calls
- **System Status:** Cache system status between checks
- **Frequency Data:** Cache current frequency setting

This API provides comprehensive real-time integration capabilities for logging software with efficient SSE-based communication and comprehensive REST endpoints for all functionality.
