@echo off
REM CTF Solver Frontend Startup Script (Windows)
REM This script will start the frontend development server
REM If you need the proxy server, please run start_proxy.bat separately

echo ========================================
echo CTF Solver Frontend Startup Script
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Start frontend development server
call start_frontend_dev.bat
