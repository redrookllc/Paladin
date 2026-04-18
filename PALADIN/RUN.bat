@echo off
setlocal enabledelayedexpansion
title Red Rook — AI Trading Platform

cls
color 07

echo.
echo.
echo          ^+----------------------------------------------------------^+
echo          ^|                                                          ^|
echo          ^|              R E D   R O O K                            ^|
echo          ^|         AI-Powered Trading Intelligence Platform         ^|
echo          ^|                                                          ^|
echo          ^+----------------------------------------------------------^+
echo.
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
python -m pip install -q --upgrade pip setuptools wheel

echo          [ 4 / 5 ]  Connecting to data feeds...
pip install -q plotly pyinstaller gpt4all tensorflow pandas numpy yfinance scikit-learn 2>nul

echo          [ 5 / 5 ]  Preparing charts...
echo.
echo          ----------------------------------------------------------
echo          STATUS  ^|  Model ready  *  Feed connecting  *  LLM standby
echo          ----------------------------------------------------------
echo.
echo.

python main.py

if errorlevel 1 (
    echo.
    echo          [ERROR]  Application exited unexpectedly.
    echo                   Check that main.py exists in this folder.
    echo.
)

pause