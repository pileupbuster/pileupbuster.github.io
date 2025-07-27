# 📡 **Sending Current QSO from Logging Software via WebSocket**

This document explains how to send current QSO (contact) information from your logging software to the Pileup Buster API via WebSocket. This shows your contacts on the frontend in real-time without affecting the queue.

## **🎯 Current QSO Integration**

**Purpose**: Show on the frontend what you're currently working from your logging software

**Key Points**:
- ✅ Shows on frontend as "🎯 Worked Direct" 
- ✅ Displays frequency, mode, and callsign info in real-time
- ❌ Does NOT add to queue
- ❌ Does NOT remove from queue
- ✅ Perfect for logging software integration
- ✅ Updates live as QSO progresses

---

## **📤 Sending Current QSO from Logging Software**

### **When to Send QSO Data**
Send QSO information to Pileup Buster in these scenarios:
- ✅ **When you start a new QSO** - Shows "now working" on frontend
- ✅ **When QSO details change** - Updates frequency/mode info  
- ✅ **When you complete the QSO** - Clears the display

---

## **1. 📤 Start Current QSO**

**Endpoint**: WebSocket message type `admin_start_qso`

**Authentication**: Requires valid session token

**When to Use**: Send this when you begin working a station

**Request Format**:
```json
{
  "type": "admin_start_qso",
  "request_id": "current_qso_001",
  "session_token": "your_session_token_here",
  "callsign": "JA1XYZ",
  "source": "direct",
  "frequency_mhz": 14.205,
  "mode": "SSB"
}
```

**Required Fields**:
- `type`: Must be "admin_start_qso"
- `request_id`: Unique identifier (use timestamp or counter)
- `session_token`: Your authenticated session token
- `callsign`: The callsign you're working
- `source`: Use "direct" for logging software contacts

**Optional Fields**:
- `frequency_mhz`: Current operating frequency (e.g., 14.205)
- `mode`: Operating mode ("SSB", "CW", "FT8", "RTTY", etc.)

**Success Response**:
```json
{
  "type": "success",
  "request_id": "current_qso_001",
  "message": "Direct QSO started successfully",
  "data": {
    "callsign": "JA1XYZ",
    "name": "Takeshi Yamamoto",
    "location": "Tokyo, Japan",
    "source": "direct",
    "frequency_mhz": 14.205,
    "mode": "SSB",
    "started_at": "2025-07-22T12:00:00Z",
    "started_via": "logging_software"
  }
}
```

**Error Response**:
```json
{
  "type": "error",
  "request_id": "current_qso_001",
  "error_code": "AUTHENTICATION_REQUIRED",
  "message": "Valid session token required"
}
```

---

## **2. 📋 Complete Current QSO**

**Endpoint**: WebSocket message type `admin_complete_qso`

**Authentication**: Requires valid session token

**When to Use**: Send this when you finish the QSO and log the contact

**Request Format**:
```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_001",
  "session_token": "your_session_token_here"
}
```

**Required Fields**:
- `type`: Must be "admin_complete_qso"
- `request_id`: Unique identifier
- `session_token`: Your authenticated session token

**Success Response**:
```json
{
  "type": "success",
  "request_id": "complete_001",
  "message": "QSO completed successfully",
  "data": {
    "callsign": "JA1XYZ",
    "source": "direct",
    "completed_at": "2025-07-22T12:05:00Z",
    "duration_minutes": 5,
    "removed_from_queue": false
  }
}
```

**Error Response**:
```json
{
  "type": "error",
  "request_id": "complete_001",
  "error_code": "NO_ACTIVE_QSO",
  "message": "No active QSO to complete"
}
```

---

## **3. 🔔 Real-time Frontend Updates**

When you send QSO data, all connected Pileup Buster clients automatically receive updates:

**QSO Started Broadcast**:
```json
{
  "type": "qso_update",
  "timestamp": "2025-07-22T12:00:00Z",
  "action": "qso_started",
  "data": {
    "callsign": "JA1XYZ",
    "name": "Takeshi Yamamoto",
    "location": "Tokyo, Japan",
    "source": "direct",
    "frequency_mhz": 14.205,
    "mode": "SSB",
    "started_via": "logging_software",
    "display_text": "🎯 Worked Direct"
  }
}
```

**QSO Completed Broadcast**:
```json
{
  "type": "qso_update",
  "timestamp": "2025-07-22T12:05:00Z",
  "action": "qso_completed",
  "data": {
    "callsign": "JA1XYZ",
    "source": "direct",
    "completed_by": "logging_software",
    "duration_minutes": 5
  }
}
```

---

## **4. 🎯 Implementation Guide for AI**

### **Step-by-Step Integration**

**Step 1: Detect New QSO**
```
When your logging software detects a new QSO starting:
- Get current callsign from your log entry
- Get current frequency from radio/rig control
- Get current mode from radio/rig control
- Send admin_start_qso message
```

**Step 2: Send Start QSO Message**
```json
{
  "type": "admin_start_qso",
  "request_id": "qso_" + timestamp,
  "session_token": stored_session_token,
  "callsign": current_callsign,
  "source": "direct",
  "frequency_mhz": current_frequency,
  "mode": current_mode
}
```

**Step 3: Handle Response**
```
If response.type == "success":
    - QSO is now showing on Pileup Buster frontend
    - Continue with normal logging
If response.type == "error":
    - Log the error
    - Continue with normal logging (don't block QSO)
```

**Step 4: Complete QSO**
```
When QSO is finished and logged:
- Send admin_complete_qso message
- Clear the display on Pileup Buster frontend
```

**Step 5: Send Complete QSO Message**
```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_" + timestamp,
  "session_token": stored_session_token
}
```

### **Error Handling**

**Authentication Errors**:
```
If error_code == "AUTHENTICATION_REQUIRED":
    - Re-authenticate with WebSocket
    - Retry the QSO message
    - Continue logging if re-auth fails
```

**Network Errors**:
```
If WebSocket connection fails:
    - Continue normal logging operation
    - Attempt to reconnect in background
    - Don't block QSO operations
```

### **Integration Points in Your Logging Software**

**1. QSO Start Trigger**:
- When user clicks "New QSO" button
- When callsign field gets focus
- When frequency changes during QSO setup
- When mode changes during QSO setup

**2. QSO Complete Trigger**:
- When user clicks "Log QSO" button
- When QSO is saved to log database
- When user starts a new QSO (complete previous one first)

**3. Frequency/Mode Updates**:
- Send new `admin_start_qso` when frequency changes
- Send new `admin_start_qso` when mode changes
- This updates the display with current info

### **Complete Code Flow Example**

```
1. User starts new QSO with JA1XYZ on 14.205 SSB
   ↓
2. Send admin_start_qso message to Pileup Buster
   ↓
3. Receive success response
   ↓
4. Frontend now shows "🎯 Worked Direct - JA1XYZ - 14.205 MHz SSB"
   ↓
5. User completes QSO and clicks "Log"
   ↓
6. Send admin_complete_qso message
   ↓
7. Receive success response
   ↓
8. Frontend clears the display
```

### **Benefits of Integration**

- ✅ **Real-time visibility**: Others can see what you're working
- ✅ **Frequency coordination**: Shows current operating frequency
- ✅ **Mode awareness**: Displays current operating mode
- ✅ **Non-intrusive**: Doesn't affect your normal logging workflow
- ✅ **Error tolerant**: Logging continues even if Pileup Buster is offline

### **Key Implementation Notes**

1. **Always use `source: "direct"`** for logging software contacts
2. **Don't block logging operations** if WebSocket fails
3. **Handle authentication errors** gracefully with retry logic
4. **Update display** when frequency/mode changes during QSO
5. **Complete previous QSO** before starting new one
6. **Use unique request IDs** to track message responses

---

## **5. 🚀 Quick Reference**

### **Typical Integration Workflow**

```json
// When QSO starts
{
  "type": "admin_start_qso",
  "request_id": "qso_12345",
  "session_token": "your_token",
  "callsign": "VK3ABC", 
  "source": "direct",
  "frequency_mhz": 21.300,
  "mode": "CW"
}

// When QSO completes
{
  "type": "admin_complete_qso",
  "request_id": "complete_12345",
  "session_token": "your_token"
}
```

### **Frontend Display Result**
- **During QSO**: Shows "🎯 Worked Direct - VK3ABC - 21.300 MHz CW"
- **After completion**: Display clears, ready for next QSO

This integration allows your logging software to seamlessly share current QSO activity with Pileup Buster while maintaining normal logging operations!
