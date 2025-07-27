# WebSocket Endpoint: `admin_ping`

## Purpose
The `admin_ping` WebSocket endpoint provides an authenticated health check for admin users. It allows your application to verify both the connection and authentication status with the backend server.

---

## How It Works

1. **Authenticate**: First, authenticate via the WebSocket API and obtain a `session_token`.
2. **Send a Ping**: Send an `admin_ping` message with your session token.
3. **Receive a Response**: The backend replies with a `success` message containing `message: "pong"` and metadata.

---

## Example Usage

### Request
```json
{
  "type": "admin_ping",
  "request_id": "your_unique_id",
  "session_token": "your_session_token"
}
```

### Response
```json
{
  "type": "success",
  "request_id": "your_unique_id",
  "message": "pong",
  "data": {
    "server_time": "2025-07-25T14:30:00Z",
    "authenticated": true,
    "ping_type": "admin_authenticated"
  }
}
```

---

## Use Cases
- **Connection health check** for admin/logging software
- **Periodic status check** to ensure authentication is still valid
- **Troubleshooting** WebSocket connectivity or session expiry

---

## Notes
- If authentication fails or the session token is invalid/expired, you will receive an error response instead of `success`.
- This endpoint is for admin/authenticated clients. For public clients, use the standard `ping`/`pong` message types.

---

**This endpoint is ideal for confirming both connection and admin authentication are working as expected.**
