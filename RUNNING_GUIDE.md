# Running and Debugging Pileup Buster

## Quick Start Guide

### Prerequisites
1. **Python 3.9+** with Poetry installed
2. **Node.js 18+** with npm
3. **MongoDB** (local or MongoDB Atlas)
4. **VS Code** with Python and JavaScript Debugger extensions

### Environment Setup

1. **Backend Setup**:
   ```powershell
   cd backend
   poetry install
   copy .env.example .env
   # Edit .env with your MongoDB URI and credentials
   ```

2. **Frontend Setup**:
   ```powershell
   cd frontend
   npm install
   ```

## Running the Application

### Method 1: Using VS Code Launch Configurations (Recommended)

1. **Start Backend Only**:
   - Press `F5` or go to Run and Debug view
   - Select "Start Backend (Poetry)" from dropdown
   - This runs the backend in debug mode on http://localhost:8000

2. **Start Frontend Only**:
   - Select "Start Frontend (npm dev)" from dropdown
   - This runs the frontend development server on http://localhost:5173

3. **Start Full Stack** (Both Frontend and Backend):
   - Select "Full Stack Debug" from dropdown
   - This starts both services simultaneously

4. **Debug Backend with Breakpoints**:
   - Select "Debug FastAPI Backend" from dropdown
   - Set breakpoints in Python code
   - Backend will pause at breakpoints for debugging

### Method 2: Using VS Code Tasks

1. **Install Dependencies**:
   - Press `Ctrl+Shift+P` → "Tasks: Run Task"
   - Select "poetry-install-backend" and "npm-install-frontend"

2. **Start Services**:
   - Run task "poetry-start-backend" for backend
   - Run task "npm-dev-frontend" for frontend

### Method 3: Manual Terminal Commands

1. **Backend**:
   ```powershell
   cd backend
   poetry run start
   ```

2. **Frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```

## Testing the QSO Logging Integration

### Using the Test Scripts

1. **Test HTTP POST Integration**:
   ```powershell
   python test_http_logging.py
   ```

2. **Test UDP Bridge** (if using bridge):
   ```powershell
   .\testUDP.ps1
   ```

### Manual Testing

1. **Start the backend** using any method above
2. **Send a test QSO** using PowerShell:
   ```powershell
   $body = @{
       callsign = "W1AW"
       frequency = "14.205"
       mode = "SSB"
       timestamp = "2024-01-15T10:30:00Z"
   } | ConvertTo-Json

   Invoke-RestMethod -Uri "http://localhost:8000/api/admin/qso/logging-direct" -Method POST -Body $body -ContentType "application/json"
   ```

## Troubleshooting

### Common Issues

1. **Launch configurations not working**:
   - Ensure Poetry virtual environment is created: `cd backend && poetry install`
   - Check Python interpreter in VS Code status bar
   - Verify npm dependencies: `cd frontend && npm install`

2. **Backend fails to start**:
   - Check MongoDB connection in `.env` file
   - Verify Poetry is installed: `poetry --version`
   - Check if port 8000 is already in use

3. **Frontend fails to start**:
   - Verify Node.js version: `node --version` (should be 18+)
   - Clear npm cache: `npm cache clean --force`
   - Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

4. **Python interpreter issues**:
   - VS Code should auto-detect the Poetry virtual environment
   - Manually select interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose the one in `backend/.venv/Scripts/python.exe`

### Debug Configuration Details

The launch configurations support:
- **Breakpoint debugging** in both Python and TypeScript/JavaScript
- **Hot reload** for both frontend and backend during development
- **Environment variable** loading from `.env` files
- **Concurrent execution** for full-stack debugging

### Environment Variables

Required in `backend/.env`:
```
MONGO_URI=mongodb://localhost:27017/pileupbuster
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
```

Optional:
```
QRZ_USERNAME=your-qrz-username
QRZ_PASSWORD=your-qrz-password
MAX_QUEUE_SIZE=50
```

## Development Workflow

1. **Start with "Full Stack Debug"** configuration for general development
2. **Use "Debug FastAPI Backend"** when debugging server-side logic
3. **Use individual configurations** when working on specific components
4. **Run tests** using VS Code test runner or `poetry run pytest` in backend directory

## API Documentation

With the backend running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **OpenAPI schema**: http://localhost:8000/openapi.json
- **Queue status**: http://localhost:8000/api/queue/status

## Integration with Logging Software

The application now accepts QSO data via HTTP POST to `/api/admin/qso/logging-direct`. This endpoint:
- Accepts QSO data in JSON format
- Processes callsign lookups via QRZ.com
- Adds stations to the queue automatically
- Broadcasts updates to connected clients
- Does not require authentication (designed for localhost use)

Example QSO data format:
```json
{
    "callsign": "W1AW",
    "frequency": "14.205",
    "mode": "SSB",
    "timestamp": "2024-01-15T10:30:00Z"
}
```
