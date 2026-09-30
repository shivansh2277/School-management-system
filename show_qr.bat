@echo off
title Sunrise School ERP - Mobile QR Code
cd /d "%~dp0"

echo ====================================================
echo   Sunrise School ERP - Mobile QR Code Generator
echo ====================================================
echo.

:: 1. Auto-detect IP, update .env, and generate QR code
call .venv\Scripts\python.exe scripts\generate_qr.py
echo.

:: 2. Open QR code image
if exist expo_qr_code.png (
    echo [*] Opening QR code image...
    start "" expo_qr_code.png
)

echo Done. Scan the QR code in Expo Go.
pause
