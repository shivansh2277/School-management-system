@echo off
title Sunrise School ERP - Full Stack Dev Launcher
setlocal enabledelayedexpansion

:: ---------------------------------------------------------
:: 0. Directory & Environment Detection
:: ---------------------------------------------------------
:: Navigate to project root whether invoked from root or school-management-system
if exist "%~dp0school-management-system\backend" (
    cd /d "%~dp0school-management-system"
) else (
    cd /d "%~dp0"
)

cls
echo ===============================================================================
echo                SUNRISE SCHOOL ERP - FULL STACK DEV LAUNCHER
echo ===============================================================================
echo.
echo [*] Working Directory: %CD%

:: Locate Python Virtual Environment
if exist "%CD%\.venv\Scripts\python.exe" (
    set "PY_EXE=%CD%\.venv\Scripts\python.exe"
) else if exist "%CD%\..\.venv\Scripts\python.exe" (
    set "PY_EXE=%CD%\..\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)
echo [*] Using Python: %PY_EXE%

:: ---------------------------------------------------------
:: 1. Auto-detect LAN IP, update .env & generate QR Codes
:: ---------------------------------------------------------
echo.
echo [*] Detecting active LAN IP and configuring environment...
"%PY_EXE%" scripts\generate_qr.py
if errorlevel 1 (
    echo [!] Warning: Failed to run scripts\generate_qr.py. Check Python dependencies.
)
echo.

:: ---------------------------------------------------------
:: 2. Port Check Warnings
:: ---------------------------------------------------------
netstat -ano | findstr /R /C:":8000 " >nul 2>&1
if not errorlevel 1 (
    echo [!] Notice: Port 8000 has an active listener. If the backend fails to bind,
    echo     close previous python/uvicorn instances or check Task Manager.
)

netstat -ano | findstr /R /C:":5173 " >nul 2>&1
if not errorlevel 1 (
    echo [!] Notice: Port 5173 has an active listener. Vite will use 5173 or next port.
)

netstat -ano | findstr /R /C:":8081 " >nul 2>&1
if not errorlevel 1 (
    echo [!] Notice: Port 8081 has an active listener. Metro will use 8081 or next port.
)

:: ---------------------------------------------------------
:: 3. Launch Servers in Dedicated Terminal Windows
:: ---------------------------------------------------------
echo.
echo [*] Launching FastAPI Backend on 0.0.0.0:8000...
start "Sunrise ERP - Backend (Port 8000)" cmd /k "cd /d "%CD%\backend" && "%PY_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [*] Launching Web ERP (Vite) on 0.0.0.0:5173...
start "Sunrise ERP - Web (Port 5173)" cmd /k "cd /d "%CD%\web" && npm run dev -- --host 0.0.0.0"

echo [*] Launching Expo Metro Bundler on port 8081 (Interactive Mode / Watch Enabled)...
start "Sunrise ERP - Mobile Expo (Port 8081)" cmd /k "cd /d "%CD%\mobile" && npx expo start --lan -c"

:: ---------------------------------------------------------
:: 4. Open Interactive Portal & QR Codes
:: ---------------------------------------------------------
echo.
if exist "test_links.html" (
    echo [*] Opening test_links.html portal in your default browser...
    start "" "test_links.html"
)

if exist "combined_qr_codes.png" (
    echo [*] Opening combined QR code image for phone scanning...
    start "" "combined_qr_codes.png"
) else if exist "expo_qr_code.png" (
    echo [*] Opening Expo QR code image...
    start "" "expo_qr_code.png"
)

:: ---------------------------------------------------------
:: 5. Credentials & Phone Quick-Start Guide
:: ---------------------------------------------------------
echo.
echo ===============================================================================
echo                      ALL SERVERS STARTED SUCCESSFULLY!
echo ===============================================================================
echo.
echo  --- HOW TO RUN ON YOUR PHYSICAL PHONE ---
echo  1. Ensure your phone and this computer are connected to the SAME Wi-Fi network.
echo  2. On Android: Open the Expo Go app and tap "Scan QR code" to scan the screen.
echo  3. On iOS: Open the native Camera app and point it at the Expo QR code.
echo.
echo  --- MOBILE APP LOGIN CREDENTIALS (Expo Go) ---
echo  -----------------------------------------------------------------------------
echo   Role Tab   ^| Login Identifier  ^| Password     ^| Key Features
echo  -----------------------------------------------------------------------------
echo   Teacher    ^| TCH001            ^| Teacher@123  ^| Marks, Attendance, Stock
echo   Parent     ^| 9876500001        ^| Parent@123   ^| CBSE Cards, Direct UPI Pay
echo   Student    ^| 2024000001        ^| Student@123  ^| Timetable, Marks, Homework
echo  -----------------------------------------------------------------------------
echo.
echo  --- WEB ERP CREDENTIALS (http://localhost:5173 or LAN IP) ---
echo   Admin: admin@sunrisepublic.edu / Admin@123
echo.
echo  --- USEFUL EXPO KEYBOARD SHORTCUTS (in Mobile window) ---
echo   [r] Reload app on phone
echo   [c] Show Metro QR code in terminal
echo   [a] Open on connected Android device/emulator
echo   [i] Open on iOS simulator
echo   [w] Open in web browser
echo.
echo ===============================================================================
echo  Keep this window open or press any key to exit this launcher (servers will keep running).
pause >nul
