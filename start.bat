@echo off
title Minecraft Server Wrapper

echo Minecraft Server Launcher
echo --------------------------
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Download Python from:
    echo https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b
)

echo Python found.

:: First-time dependency install
if not exist setup_done.txt (
    echo.
    echo First run detected.
    echo Installing Python dependencies from requirement.txt...
    echo.

    python -m pip install --upgrade pip
    python -m pip install -r requirement.txt

    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies.
        pause
        exit /b
    )

    :: Write fixed ISO-8601 timestamp (reliable)
    powershell -NoProfile -Command ^
      "Get-Date -Format 'yyyy-MM-ddTHH:mm:ss' | Out-File -Encoding ASCII setup_done.txt"

    echo Dependencies installed.
)

echo.
echo Starting Minecraft server...
echo.

python run.py

echo.
echo Server process ended.
pause
