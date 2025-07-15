# Debug Configuration Troubleshooting

## Current Issues and Solutions

### Issue 1: Full Stack Debug Configurations Not Working

**Problem**: The VS Code launch configurations for debugging the full stack are failing.

**Root Causes**:
1. **debugpy not installed**: The Python debugger module is missing from the Poetry virtual environment
2. **Path resolution issues**: VS Code having trouble finding the correct Python interpreter
3. **Network connectivity**: Unable to install debugpy due to PyPI connection issues

### Solutions

#### Option 1: Manual Terminal Method (Currently Working)

**Backend**:
```powershell
cd C:\Users\DJDaithi\Documents\Source\pileupbuster.github.io\backend
poetry run start
```

**Frontend** (separate terminal):
```powershell
cd C:\Users\DJDaithi\Documents\Source\pileupbuster.github.io\frontend
npm run dev
```

#### Option 2: Install debugpy Manually

```powershell
cd C:\Users\DJDaithi\Documents\Source\pileupbuster.github.io\backend
poetry shell
pip install debugpy
```

#### Option 3: Use VS Code Tasks Instead of Launch Configs

1. Open VS Code Command Palette (`Ctrl+Shift+P`)
2. Select "Tasks: Run Task"
3. Choose "poetry-start-backend"
4. In another terminal, choose "npm-dev-frontend"

### Current Working Launch Configurations

The simplified `launch.json` now contains:

1. **Debug FastAPI Backend (Uvicorn)**: Uses uvicorn module directly
2. **Start Backend (Direct)**: Runs app.py directly
3. **Start Frontend (NPM Dev)**: Uses npm run dev
4. **Full Stack Debug (Simple)**: Combines backend and frontend
5. **Full Stack Start (Direct)**: Alternative method

### Testing the Configurations

To test if the launch configurations work:

1. **Try "Start Backend (Direct)"** first
2. If it works, try **"Full Stack Start (Direct)"**
3. If debugpy issues persist, use the manual terminal method

### Expected Behavior

When working correctly:
- **Backend**: Should start on http://localhost:8000
- **Frontend**: Should start on http://localhost:5173 (or next available port)
- **Both**: Should have hot-reload enabled for development

### Debugging Tips

1. **Check Python Interpreter**: 
   - Press `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose: `C:\Users\DJDaithi\Documents\Source\pileupbuster.github.io\backend\.venv\Scripts\python.exe`

2. **Verify Dependencies**:
   ```powershell
   cd backend
   poetry install
   cd ../frontend
   npm install
   ```

3. **Port Conflicts**: If ports are in use:
   ```powershell
   netstat -ano | findstr ":8000"
   netstat -ano | findstr ":5173"
   ```

4. **Clear VS Code Cache**: 
   - Restart VS Code
   - Clear terminal sessions
   - Reload window (`Ctrl+Shift+P` → "Developer: Reload Window")

### Alternative: Docker Compose

As a fallback, you can use Docker:
```powershell
cd C:\Users\DJDaithi\Documents\Source\pileupbuster.github.io\backend
docker-compose up -d
```

## Network and Dependency Issues

### PyPI Connection Problems

If you encounter PyPI connection issues:

1. **Check internet connection**
2. **Try different network** (e.g., mobile hotspot)
3. **Use offline mode**: `poetry install --no-dev` (if packages already cached)
4. **Use pip directly** in Poetry shell:
   ```powershell
   poetry shell
   pip install debugpy --index-url https://pypi.org/simple/
   ```

### VS Code Extension Issues

1. **Python Extension**: Ensure Python extension is installed and enabled
2. **Debugger Extension**: JavaScript Debugger should be built-in
3. **Reload Extensions**: `Ctrl+Shift+P` → "Developer: Reload Window"

## Quick Start (When Everything Works)

1. **Open VS Code** in the project root
2. **Press F5** or go to Run and Debug
3. **Select "Full Stack Debug (Simple)"**
4. **Both services should start** with debugging enabled

## Current Status

- ✅ Manual terminal method works
- ✅ VS Code tasks configured
- ⚠️ Launch configurations need debugpy
- ⚠️ Network issues preventing debugpy installation
- ✅ Application functionality intact
- ✅ HTTP POST integration working
