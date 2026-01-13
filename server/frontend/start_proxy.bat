@echo off
REM CTF Solver Frontend Proxy Server Startup Script (Windows)
REM Usage: start_proxy.bat [port]
REM Default port: 8081

echo ========================================
echo CTF Solver Frontend Proxy Server
echo ========================================
echo.

REM Check if proxy_server.py exists
if not exist "proxy_server.py" (
    echo Error: proxy_server.py not found
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if requests module is installed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Warning: requests module not installed. Installing now...
    pip install requests
    if errorlevel 1 (
        echo Error: Failed to install requests
        pause
        exit /b 1
    )
)

REM Get port number parameter
set PORT=%1
if "%PORT%"=="" set PORT=8081

echo Starting proxy server...
echo Proxy server port: %PORT%
echo Backend API address: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python proxy_server.py %PORT%

pause
