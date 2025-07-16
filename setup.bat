@echo off
REM SEC Filing Scanner - Windows Setup Launcher
REM This batch file provides an easy way to run the setup on Windows

echo ========================================
echo SEC Filing Scanner - Setup Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8-3.11 from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Starting setup launcher...
echo.

REM Run the Python setup launcher
python setup_launcher.py

REM Check if setup was successful
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Setup process completed
    echo ========================================
    echo.
    echo To run the application:
    echo 1. Backend: uvicorn app.main:app --reload
    echo 2. Frontend: streamlit run streamlit_app.py
    echo.
) else (
    echo.
    echo ========================================
    echo Setup encountered issues
    echo ========================================
    echo.
    echo Please check the error messages above
    echo and refer to SETUP_README.md for help
    echo.
)

pause
