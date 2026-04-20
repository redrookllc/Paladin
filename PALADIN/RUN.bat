@echo off
setlocal enabledelayedexpansion
title Paladin — AI Trading Platform

cls
color 07
echo.
echo.
echo          ============================================================
echo                         ____        _           _ _       
echo                        |  _ \ __ _ | | __ _  __| (_)_ __  
echo                        | |_) / _` || |/ _` |/ _` | | '_ \ 
echo                        |  __/ (_| || | (_| | (_| | | | | |
echo                        |_|   \__,_||_|\__,_|\__,_|_|_| |_|
echo          ------------------------------------------------------------
echo                  AI-Powered Trading Intelligence Platform
echo          ============================================================
echo.

cd /d "%~dp0"

echo          [ 1 / 5 ]  Initialising engine...
if not exist red_trader (
    echo          [ 1 / 5 ]  Creating virtual environment...
    python -m venv red_trader
    if errorlevel 1 (
        echo.
        echo          [ERROR]  Failed to create virtual environment.
        echo                   Ensure Python 3.11 is installed and in PATH.
        echo.
        pause
        exit /b 1
    )
)

echo          [ 2 / 5 ]  Activating environment...
call red_trader\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo          [ERROR]  Could not activate virtual environment.
    echo.
    pause
    exit /b 1
)

echo          [ 3 / 5 ]  Loading trading brain...
python -m pip install --upgrade pip setuptools wheel

echo          [ 4 / 5 ]  Connecting to data feeds...
if exist requirements.txt (
    echo          [ 4 / 5 ]  Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo          [WARNING] requirements.txt not found. Skipping dependency install.
)

echo          [ 5 / 5 ]  Preparing charts...
echo.
echo          ----------------------------------------------------------
echo          STATUS  ^|  Model ready  *  Feed connecting  *  LLM standby
echo          ----------------------------------------------------------
echo.
echo.

REM --- Launch desktop app ---
python main.py

if errorlevel 1 (
    echo.
    echo          [ERROR]  Application exited unexpectedly.
    echo                   Check that main.py exists in this folder.
    echo.
)

pause
