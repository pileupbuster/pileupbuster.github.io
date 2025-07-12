@echo off
echo QLog Bridge Starter
echo ===================
echo.
echo Installing dependencies...
pip install websockets
echo.
echo Starting QLog Bridge...
echo UDP Port: 2238
echo WebSocket Port: 8765
echo.
echo Configure QLog to send UDP to 127.0.0.1:2238
echo.
python -m bridge.main
pause
