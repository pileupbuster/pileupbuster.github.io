# Pileup Buster Integration - Build Requirements

## Overview
Two HTTP-based functions required for bidirectional integration between logging software and Pileup Buster. No firewall configuration needed - uses standard outbound HTTP requests only.

## Function 1: Send QSO to Pileup Buster

### Purpose
Notify Pileup Buster when a QSO starts in your logging software.

### Implementation Requirements
- **Method:** HTTP POST
- **URL:** `http://localhost:8000/api/admin/qso/logging-direct`
- **Headers:** `Content-Type: application/json`
- **Timeout:** 10 seconds recommended
- **Trigger:** When user finalizes a callsign for QSO

### Required Payload Format
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

### Field Requirements
- **`type`:** Always `"qso_start"`
- **`callsign`:** Target callsign (required)
- **`source`:** Always `"pblog_native"`
- **`timestamp`:** Current time in ISO 8601 format (required)
- **`triggered_by`:** Always `"callsign_finalized"`
- **`frequency_mhz`:** Operating frequency in MHz (optional)
- **`mode`:** Operating mode like "SSB", "CW", "FT8" (optional)

### Success Response
- **HTTP 200** with acknowledgment JSON data
- Response includes confirmation of QSO start

### Error Handling
- **HTTP 400:** Invalid payload format
- **HTTP 503:** System inactive or integration disabled
- **Connection refused:** Pileup Buster not running
- **Timeout:** Network or backend issues

## Function 2: Monitor Pileup Buster for QSOs

### Purpose
Detect new QSOs started in Pileup Buster and automatically add them to your log.

### Implementation Requirements
- **Method:** HTTP GET polling
- **Poll Interval:** 3-5 seconds for responsive detection
- **Timeout:** 5-10 seconds per request
- **State Tracking:** Track last callsign/timestamp to detect changes

### Primary Endpoint: Current QSO
- **URL:** `http://localhost:8000/api/queue/current`
- **Returns:** Current active QSO data or `null`

### Secondary Endpoint: Queue List (Optional)
- **URL:** `http://localhost:8000/api/queue/list`
- **Returns:** All waiting users in queue
- **Use Case:** Display queue status in your software

### Current QSO Response Format
```json
{
  "callsign": "EI6LF",
  "timestamp": "2025-07-16T14:30:45Z",
  "qrz": {
    "name": "John Smith",
    "address": "Dublin, Ireland",
    "dxcc_name": "Ireland"
  },
  "metadata": {
    "frequency_mhz": 14.2715,
    "mode": "SSB",
    "source": "queue"
  }
}
```

### Detection Logic
1. **First Poll:** Initialize state with current response
2. **Subsequent Polls:** Compare with previous state
3. **New QSO:** Different callsign or timestamp = add to log
4. **QSO Completed:** Response changes to `null`
5. **No Change:** Same callsign and timestamp

### Key Response Fields
- **`callsign`:** Station being worked
- **`timestamp`:** When QSO started
- **`metadata.frequency_mhz`:** Operating frequency
- **`metadata.mode`:** Operating mode
- **`qrz.name`:** Operator name from QRZ lookup
- **`qrz.dxcc_name`:** Country/location

### Queue List Response Format
```json
{
  "queue": [
    {
      "callsign": "W1ABC",
      "position": 1,
      "timestamp": "2025-07-16T14:30:45Z",
      "qrz": { /* QRZ data */ }
    }
  ],
  "total": 1,
  "max_size": 4,
  "system_active": true
}
```

## Error Handling Strategy

### Network Errors
- **Retry Logic:** Exponential backoff for failed requests
- **Graceful Degradation:** Continue operation if integration fails
- **User Feedback:** Show connection status in UI
- **Logging:** Record integration events for debugging

### Common Error Responses
- **HTTP 503:** System inactive - retry later
- **HTTP 500:** Backend error - log and retry
- **Connection timeout:** Network issues - implement retry
- **JSON parse error:** Invalid response format

## Configuration Requirements

### Deployment Settings
- **Local Development:** `http://localhost:8000`
- **Production:** Configure base URL as needed
- **Cloud Deployment:** Use HTTPS URLs for cloud instances

### User Configuration Options
- **Enable/Disable Integration:** Allow users to toggle
- **Poll Interval:** Configurable 2-10 seconds
- **Base URL:** Allow custom Pileup Buster URLs
- **Timeout Settings:** Configurable request timeouts

## Testing Integration

### Verification Steps
1. Start Pileup Buster backend (port 8000)
2. Enable system and logger integration in Pileup Buster
3. Test Function 1: Send QSO → verify appears in Pileup Buster
4. Test Function 2: Add callsigns to queue, click "Next" → verify detection
5. Test error handling with backend stopped

### Test Endpoints
- **System Status:** `GET http://localhost:8000/api/public/status`
- **Current QSO:** `GET http://localhost:8000/api/queue/current`
- **Queue List:** `GET http://localhost:8000/api/queue/list`

## Integration Benefits

### Technical Advantages
- **Firewall-Friendly:** Only outbound HTTP requests
- **Universal Deployment:** Works in any environment
- **No Authentication:** Public endpoints for monitoring
- **Standard Protocol:** HTTP GET/POST only
- **Real-Time Responsive:** 3-5 second detection

### Operational Benefits
- **Bidirectional Sync:** QSOs flow both directions automatically
- **Queue Visibility:** See waiting stations in logging software
- **Contest Ready:** Fast QSO detection for contest operation
- **Multi-Operator:** Share QSO state across multiple instances

## Implementation Priority

1. **Function 1 (Send QSO):** Start here - simpler implementation
2. **Function 2 (Monitor):** Add polling after send function works
3. **Error Handling:** Implement robust retry logic
4. **User Interface:** Add status indicators and configuration
5. **Testing:** Comprehensive integration testing

Both functions use standard HTTP and work without