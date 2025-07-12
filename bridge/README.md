# QLog Bridge

QLog Bridge is a UDP-to-WebSocket bridge that receives amateur radio QSO data from logging software (like QLog) and forwards it to web applications via WebSocket.

## Features

- **UDP Receiver**: Listens for packets from amateur radio logging software
- **Packet Parsing**: Supports WSJT-X binary format, ADIF text, and plain text
- **WebSocket Server**: Broadcasts QSO data to connected web clients
- **Multiple Format Support**: Handles various packet formats from different logging software
- **Configurable**: JSON-based configuration file
- **Logging**: Comprehensive logging for debugging
- **Auto-reconnection**: Robust connection handling

## Quick Start

### 1. Install Dependencies

```bash
pip install websockets asyncio
```

### 2. Run the Bridge

```bash
python -m bridge.main
```

### 3. Configure QLog

In QLog settings:
- **Network** → **WSJT-X** → **Raw UDP forward**: `127.0.0.1`
- **Port**: `2238`

### 4. Connect from Web Application

```javascript
const ws = new WebSocket('ws://localhost:8765');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'qso_start') {
        console.log('QSO started:', data.data.callsign);
    }
};
```

## Configuration

The bridge creates a `bridge_config.json` file with default settings:

```json
{
    "udp_port": 2238,
    "websocket_port": 8765,
    "log_level": "INFO",
    "auto_start": true,
    "buffer_size": 1024,
    "reconnect_delay": 5.0,
    "max_clients": 10
}
```

## Supported Packet Formats

### WSJT-X Binary Format
Standard WSJT-X UDP packets with magic number `0xADBCCBDA`

### ADIF Text Format
```
<call:6>W1ABC <qso_date:8>20250115 <time_on:6>203045 <mode:3>FT8 <eor>
```

### Plain Text
Simple callsign transmission:
```
W1ABC
```

## WebSocket Messages

### Outbound (Bridge → Client)

#### Welcome Message
```json
{
    "type": "welcome",
    "message": "Connected to QLog Bridge",
    "server_time": 1642262425.123
}
```

#### QSO Start
```json
{
    "type": "qso_start",
    "data": {
        "callsign": "W1ABC",
        "timestamp": "2025-01-15T20:30:45.123Z",
        "source": "adif",
        "frequency_mhz": 14.074,
        "mode": "FT8"
    }
}
```

### Inbound (Client → Bridge)

#### Ping
```json
{
    "type": "ping"
}
```

#### Status Request
```json
{
    "type": "status"
}
```

## Architecture

```
QLog → UDP (2238) → Bridge → WebSocket (8765) → Web Client
```

1. **QLog** sends UDP packets when QSO starts
2. **Bridge** receives UDP on port 2238
3. **Parser** extracts callsign and QSO data
4. **WebSocket Server** broadcasts to connected clients on port 8765
5. **Web Client** receives QSO data for processing

## Logging

Logs are written to:
- **Console**: Real-time output
- **qlog_bridge.log**: Persistent log file

Log levels: DEBUG, INFO, WARNING, ERROR

## Error Handling

- **Invalid Packets**: Logged and ignored
- **Client Disconnections**: Automatic cleanup
- **Socket Errors**: Graceful reconnection attempts
- **Parse Failures**: Fallback to alternative parsing methods

## Development

### Project Structure
```
bridge/
├── main.py              # Entry point and main application
├── config.py           # Configuration management
├── udp_receiver.py     # UDP packet reception
├── websocket_server.py # WebSocket server
└── parser.py          # Packet parsing logic
```

### Testing

Test with manual UDP packets:
```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b'<call:5>W1ABC <eor>', ('127.0.0.1', 2238))
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Change UDP/WebSocket ports in config
   - Check for other applications using ports

2. **No Packets Received**
   - Verify QLog UDP output configuration
   - Check firewall settings
   - Confirm bridge is listening on correct port

3. **WebSocket Connection Failed**
   - Ensure WebSocket port is available
   - Check browser developer console for errors
   - Verify localhost connectivity

### Debug Mode

Set log level to DEBUG in config:
```json
{
    "log_level": "DEBUG"
}
```

This provides detailed packet information and connection logs.
