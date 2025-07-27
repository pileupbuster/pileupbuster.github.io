# WebSocket Endpoint: `admin_get_status`

## Purpose
The `admin_get_status` WebSocket endpoint allows an authenticated admin client to request the current system status and key operational information from the backend. This is useful for monitoring, dashboards, or logging software that needs a snapshot of the system state.

---

## How It Works

1. **Authenticate**: First, authenticate via the WebSocket API and obtain a `session_token`.
2. **Send a Status Request**: Send an `admin_get_status` message with your session token.
3. **Receive a Response**: The backend replies with a `success` message containing the current system status and related data.

---

## Example Usage

### Request
```json
{
  "type": "admin_get_status",
  "request_id": "your_unique_id",
  "session_token": "your_session_token"
}
```

### Response
```json
{
  "type": "success",
  "request_id": "your_unique_id",
  "message": "System status retrieved successfully",
  "data": {
    "system_active": true,
    "queue": [
      {"callsign": "M0ABC", ...},
      {"callsign": "G1XYZ", ...}
    ],
    "current_qso": {"callsign": "M0ABC", ...},
    "max_queue_size": 4,
    "other_status_fields": "..."
  }
}
```

---

## Use Cases
- **Admin dashboard**: Show live system status and queue
- **Logging/monitoring**: Periodically poll for a snapshot of the system
- **Troubleshooting**: Quickly check if the system is active and what the current queue looks like

---

## Notes
- If authentication fails or the session token is invalid/expired, you will receive an error response instead of `success`.
- The exact fields in the `data` object may vary depending on backend implementation, but will always include the core system status and queue information.

---

**This endpoint is ideal for admin clients that need a one-shot, up-to-date snapshot of the system state.**
