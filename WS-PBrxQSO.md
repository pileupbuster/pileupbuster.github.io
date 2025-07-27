# 📡 **Sending Direct QSOs to Pileup Buster via WebSocket**

This document explains how to send direct QSO (contact) information from your logging program to the Pileup Buster API via WebSocket. This shows your contacts on the frontend without affecting the queue.

## **🎯 Direct QSO Operation**

**Purpose**: Show on the frontend that you're working someone directly from your logging software

**Key Points**:
- ✅ Shows on frontend as "🎯 Worked Direct" 
- ✅ Displays frequency, mode, and callsign info
- ❌ Does NOT add to queue
- ❌ Does NOT remove from queue
- ✅ Perfect for general logging integration

---

## **1. 📤 Start Direct QSO**

**Endpoint**: WebSocket message type `admin_start_qso`

**Authentication**: Requires valid session token

**Request Format**:
```json
{
  "type": "admin_start_qso",
  "request_id": "direct_qso_001",
  "session_token": "your_session_token_here",
  "callsign": "JA1XYZ",
  "source": "direct",
  "frequency_mhz": 14.205,
  "mode": "SSB"
}
```

**Success Response**:
```json
{
  "type": "success",
  "request_id": "direct_qso_001",
  "message": "Direct QSO started successfully",
  "data": {
    "callsign": "JA1XYZ",
    "name": "Takeshi Yamamoto",
    "location": "Tokyo, Japan",
    "source": "direct",
    "frequency_mhz": 14.205,
    "mode": "SSB",
    "started_at": "2025-07-21T12:00:00Z",
    "started_via": "logging_software"
  }
}
```

**Error Response**:
```json
{
  "type": "error",
  "request_id": "direct_qso_001",
  "error_code": "AUTHENTICATION_REQUIRED",
  "message": "Valid session token required"
}
```

---

## **2. 📋 Complete Direct QSO**

**Endpoint**: WebSocket message type `admin_complete_qso`

**Purpose**: Mark the direct QSO as completed

**Authentication**: Requires valid session token

**Request Format**:
```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_001",
  "session_token": "your_session_token_here"
}
```

**Success Response**:
```json
{
  "type": "success",
  "request_id": "complete_001",
  "message": "QSO completed successfully",
  "data": {
    "callsign": "JA1XYZ",
    "source": "direct",
    "completed_at": "2025-07-21T12:05:00Z",
    "duration_minutes": 5,
    "removed_from_queue": false
  }
}
```

---

## **3. 🔔 Real-time Frontend Updates**

When you start a direct QSO, all connected clients automatically receive:

**Direct QSO Started Broadcast**:
```json
{
  "type": "qso_update",
  "timestamp": "2025-07-21T12:00:00Z",
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

**Direct QSO Completed Broadcast**:
```json
{
  "type": "qso_update",
  "timestamp": "2025-07-21T12:05:00Z",
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

## **4. 🎯 AI Implementation Instructions**

### **Required Fields**
- **`callsign`**: The callsign you're working
- **`source`**: Must be "direct" for logging software
- **`session_token`**: Valid admin session token
- **`request_id`**: Unique identifier for request tracking

### **Optional Fields**
- **`frequency_mhz`**: Operating frequency (e.g., 14.205)
- **`mode`**: Operating mode (e.g., "SSB", "CW", "FT8")

### **Complete Workflow Example**

**Step 1: Start Direct QSO**
```json
{
  "type": "admin_start_qso",
  "request_id": "direct_ja1xyz_001",
  "session_token": "your_token",
  "callsign": "JA1XYZ",
  "source": "direct",
  "frequency_mhz": 21.300,
  "mode": "CW"
}
```

**Step 2: Receive Confirmation**
```json
{
  "type": "success",
  "request_id": "direct_ja1xyz_001",
  "message": "Direct QSO started successfully",
  "data": {
    "callsign": "JA1XYZ",
    "source": "direct"
  }
}
```

**Step 3: Complete QSO**
```json
{
  "type": "admin_complete_qso",
  "request_id": "complete_ja1xyz_001",
  "session_token": "your_token"
}
```

**Step 4: Receive Completion Confirmation**
```json
{
  "type": "success",
  "request_id": "complete_ja1xyz_001",
  "message": "QSO completed successfully",
  "data": {
    "callsign": "JA1XYZ",
    "source": "direct",
    "removed_from_queue": false
  }
}
```

---

## **5. 🚀 Quick Integration Guide**

### **For Your AI Program:**

1. **When starting any contact**, send `admin_start_qso` with `source: "direct"`
2. **Wait for success response** confirming the QSO started
3. **Proceed with radio contact** 
4. **After completing contact**, send `admin_complete_qso`
5. **Frontend displays** "🎯 Worked Direct" with frequency/mode info

### **Benefits:**
- ✅ **Shows all your logging activity** on Pileup Buster frontend
- ✅ **Real-time updates** for anyone watching
- ✅ **No queue interference** - purely for display
- ✅ **Frequency and mode display** shows current operating info
- ✅ **Simple integration** - works with any callsign

This provides clean integration between your logging software and Pileup Buster frontend for displaying direct contacts!
