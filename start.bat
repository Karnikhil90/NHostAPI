@echo off
title Minecraft Server Wrapper

:: Check if Python exists
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Python is NOT installed or not added to PATH.
    echo.
    echo Please download Python from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: While installing, check "Add Python to PATH"
    echo.
    pause
    exit /b
)

:: Python exists
echo Python found.
echo Starting Minecraft server...
echo.

python run.py

echo.
echo Server process ended.
pause
    