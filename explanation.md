# Logging Software HTTP Integration Guide

## Overview

This document explains how to modify your logging software to integrate directly with Pileup Buster using HTTP POST requests instead of WebSocket connections. This eliminates the need for any bridge software and provides a more reliable integration.

## What Changed

### Before (WebSocket Approach)
- Logging software acted as a WebSocket **client**
- Connected to `ws://localhost:8765`
- Required a bridge server to relay messages
- More complex setup with potential connection issues

### After (HTTP POST Approach)
- Logging software sends HTTP **POST** requests
- Sends to `http://localhost:8000/api/admin/qso/logging-direct`
- Direct integration with Pileup Buster backend
- Simpler, more reliable communication

## Required Changes in Your Logging Software

### 1. Change Protocol
**Replace WebSocket client code with HTTP POST requests**

**From:**
```python
# OLD WebSocket approach
import websockets

async def send_qso_websocket(qso_data):
    async with websockets.connect("ws://localhost:8765") as websocket:
        await websocket.send(json.dumps(qso_data))
        response = await websocket.recv()
```

**To:**
```python
# NEW HTTP POST approach
import requests

def send_qso_http(qso_data):
    response = requests.post(
        "http://localhost:8000/api/admin/qso/logging-direct",
        json=qso_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    return response.json()
```

### 2. Update Configuration Settings

**Change these settings in your logging software:**

| Setting | Old Value | New Value |
|---------|-----------|-----------|
| Protocol | WebSocket | HTTP POST |
| URL | `ws://localhost:8765` | `http://localhost:8000/api/admin/qso/logging-direct` |
| Method | WebSocket connect | HTTP POST |
| Content-Type | N/A | `application/json` |

### 3. Keep Message Format (No Changes Needed)

**The message format remains exactly the same:**

```json
{
  "type": "qso_start",
  "data": {
    "callsign": "EI6LF",
    "frequency_mhz": 14.2715,
    "mode": "SSB",
    "source": "pblog_native",
    "timestamp": "2025-07-14T18:04:47.142Z",
    "triggered_by": "callsign_finalized"
  }
}
```

### 4. Handle Response

**The HTTP response will include an acknowledgment:**

```json
{
  "type": "ack",
  "timestamp": "2025-07-14T18:04:47.142Z",
  "received": {
    "data": { /* original QSO data */ },
    "type": "qso_start"
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

## Implementation Examples

### Python Implementation
```python
import requests
import json
from datetime import datetime

class PileupBusterIntegration:
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.endpoint = f"{backend_url}/api/admin/qso/logging-direct"
    
    def send_qso_start(self, callsign, frequency_mhz=None, mode=None):
        """Send QSO start notification to Pileup Buster"""
        message = {
            "type": "qso_start",
            "data": {
                "callsign": callsign,
                "frequency_mhz": frequency_mhz,
                "mode": mode,
                "source": "pblog_native",
                "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "triggered_by": "callsign_finalized"
            }
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ QSO started for {callsign}")
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None

# Usage example
integration = PileupBusterIntegration()
integration.send_qso_start("EI6LF", 14.2715, "SSB")
```

### C# Implementation
```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class PileupBusterIntegration
{
    private readonly HttpClient _httpClient;
    private readonly string _endpoint;

    public PileupBusterIntegration(string backendUrl = "http://localhost:8000")
    {
        _httpClient = new HttpClient();
        _endpoint = $"{backendUrl}/api/admin/qso/logging-direct";
    }

    public async Task<bool> SendQsoStartAsync(string callsign, double? frequencyMhz = null, string mode = null)
    {
        var message = new
        {
            type = "qso_start",
            data = new
            {
                callsign = callsign,
                frequency_mhz = frequencyMhz,
                mode = mode,
                source = "pblog_native",
                timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
                triggered_by = "callsign_finalized"
            }
        };

        try
        {
            var json = JsonSerializer.Serialize(message);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync(_endpoint, content);
            
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadAsStringAsync();
                Console.WriteLine($"✅ QSO started for {callsign}");
                return true;
            }
            else
            {
                Console.WriteLine($"❌ Error: {response.StatusCode}");
                return false;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Network error: {ex.Message}");
            return false;
        }
    }
}

// Usage example
var integration = new PileupBusterIntegration();
await integration.SendQsoStartAsync("EI6LF", 14.2715, "SSB");
```

## Configuration Steps

### 1. In Your Logging Software Settings
1. **Find the Pileup Buster/WebSocket integration settings**
2. **Change protocol from WebSocket to HTTP POST**
3. **Update URL to:** `http://localhost:8000/api/admin/qso/logging-direct`
4. **Set Content-Type to:** `application/json`
5. **Keep the same message format**

### 2. Test the Integration
Use the provided test scripts to verify the integration works:

**Python Test:**
```bash
python test_http_logging.py EI6LF 14.2715 SSB
```

**PowerShell Test:**
```powershell
.\test_http_logging.ps1 EI6LF 14.2715 SSB
```

### 3. Verify in Pileup Buster
1. **Open Pileup Buster frontend**
2. **Enable HTTP POST integration** in the Bridge Status section
3. **Send a test QSO from your logging software**
4. **Verify the QSO appears** in the current QSO section

## Error Handling

### Common HTTP Status Codes
- **200 OK**: QSO processed successfully
- **400 Bad Request**: Invalid message format or missing required fields
- **500 Internal Server Error**: Backend processing error

### Connection Issues
- **Connection Refused**: Backend not running (start with `poetry run start`)
- **Timeout**: Request took too long (check network/backend performance)
- **DNS Error**: Wrong hostname (use `localhost` or correct IP)

## Benefits of HTTP POST Approach

1. **Reliability**: HTTP is more reliable than WebSocket for one-way communication
2. **Simplicity**: No need to maintain persistent connections
3. **Error Handling**: Standard HTTP status codes for error handling
4. **Debugging**: Easier to debug with standard HTTP tools
5. **No Bridge**: Direct integration eliminates bridge software complexity

## Migration Checklist

- [ ] Update logging software protocol from WebSocket to HTTP POST
- [ ] Change URL to `http://localhost:8000/api/admin/qso/logging-direct`
- [ ] Keep existing message format
- [ ] Add proper error handling for HTTP responses
- [ ] Test with the provided test scripts
- [ ] Verify integration in Pileup Buster frontend
- [ ] Remove any WebSocket bridge software

## Support

If you encounter issues during the migration:

1. **Test with the provided scripts** to verify the backend is working
2. **Check the browser console** in Pileup Buster for any error messages
3. **Check the backend logs** for processing errors
4. **Verify your logging software** is sending the correct HTTP POST format

The HTTP POST approach provides a much more reliable and simpler integration with Pileup Buster!
