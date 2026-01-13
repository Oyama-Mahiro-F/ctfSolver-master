@echo off
REM CTF Solver Frontend Development Server Startup Script (Windows)
REM Usage: start_frontend_dev.bat

echo ========================================
echo CTF Solver Frontend Development Server
echo ========================================
echo.

REM Check if we are in the correct directory
if not exist "package.json" (
    echo Error: package.json not found. Please run this script in the frontend directory.
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo Dependencies not installed. Installing now...
    echo.
    call npm install
    if errorlevel 1 (
        echo Error: npm install failed
        pause
        exit /b 1
    )
    echo.
)

echo Starting frontend development server...
echo Frontend will be available at http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev

pause
