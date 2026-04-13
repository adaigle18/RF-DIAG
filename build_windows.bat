@echo off
REM build_windows.bat — Build RF-DIAG.exe for Windows
REM Run from the project folder on a Windows machine

echo RF-DIAG Windows Build
echo =====================
echo.

REM Install dependencies
echo Installing dependencies...
pip install flask paramiko pyinstaller
echo.

REM Clean previous build
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

REM Build
echo Building RF-DIAG.exe...
python -m PyInstaller RF_DIAG_Windows.spec --noconfirm

echo.
echo Build complete: dist\RF-DIAG\RF-DIAG.exe
echo.
echo To run:
echo   dist\RF-DIAG\RF-DIAG.exe
echo.
echo Your browser will open automatically at http://127.0.0.1:5001
