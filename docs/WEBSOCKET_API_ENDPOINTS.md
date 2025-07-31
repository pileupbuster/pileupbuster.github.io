# WebSocket API Endpoints (Admin and Public)

This document lists the main WebSocket API message types ("endpoints") for Pileup Buster, including both admin and public operations. For full protocol details, see the main API documentation.

## Admin WebSocket Message Types

- `admin_get_queue` — Get the current queue (admin only)
- `admin_complete_qso` — Complete the current QSO (admin only)
- `admin_cancel_qso` — Cancel the current QSO (admin only)
- `admin_work_next` — Advance to the next callsign in the queue (admin only)
- `admin_work_specific` — Work a specific callsign from the queue (admin only)
- `admin_start_qso` — Start a QSO manually (admin only)
- `admin_set_frequency` — Set the current frequency (admin only)
- `admin_clear_frequency` — Clear the current frequency (admin only)
- `admin_set_split` — Set the current split value (admin only)
- `admin_clear_split` — Clear the current split value (admin only)
- `admin_toggle_system` — Activate or deactivate the system (admin only)
- `admin_get_status` — Get the current system status (admin only)
- `admin_get_current_qso` — Get the current QSO (admin only)
- `admin_ping` — Ping for admin connection testing

## Public/System WebSocket Message Types

- `auth_request` — Request authentication (send credentials/token)
- `auth_response` — Authentication result
- `register_callsign` — Register a callsign in the queue
- `success` — Generic success response
- `error` — Generic error response
- `queue_update` — Broadcast: queue has changed
- `qso_update` — Broadcast: QSO has changed
- `system_status_update` — Broadcast: system status has changed
- `ping` — Ping (public)
- `pong` — Pong (public)

**Note:**
- All admin message types require a valid admin session (token-based authentication).
- For payload schemas and detailed usage, see `backend/app/websocket_protocol.py` and `docs/WEBSOCKET_API_DOCUMENTATION.md`.
