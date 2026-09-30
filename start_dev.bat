@echo off
title Sunrise School ERP - Dev Launcher
cd /d "%~dp0"

echo ====================================================
echo   Sunrise School ERP - Full Stack Dev Launcher
echo ====================================================
echo.

:: 1. Auto-detect IP, update .env, and generate QR code
echo [*] Detecting network IP and generating QR code...
call .venv\Scripts\python.exe scripts\generate_qr.py
echo.

:: 2. Launch Backend in separate window
echo [*] Launching FastAPI Backend on port 8000...
start "Sunrise ERP - Backend (Port 8000)" cmd /k "cd /d %~dp0backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 3. Launch Web ERP Frontend in separate window
echo [*] Launching Web ERP on port 5173...
start "Sunrise ERP - Web (Port 5173)" cmd /k "cd /d %~dp0web && npm run dev -- --host"

:: 4. Launch Expo Metro Bundler in separate window
echo [*] Launching Expo Metro Bundler on port 8081...
start "Sunrise ERP - Mobile Expo (Port 8081)" cmd /k "cd /d %~dp0mobile && set CI=1 && npx expo start --lan -c"

:: 5. Open the QR code image
if exist expo_qr_code.png (
    echo [*] Opening QR code image for scanning...
    start "" expo_qr_code.png
)

echo.
echo ====================================================
echo   All servers started successfully in new windows!
echo   Scan the QR code with Expo Go on your phone.
echo ====================================================
pause
