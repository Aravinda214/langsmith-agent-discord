@echo off
REM Setup script for Discord Channel Selector
REM This script automates the initial setup process

echo ========================================
echo Discord Channel Selector - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python found
python --version

REM Create virtual environment
echo.
echo [2/5] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Setup .env file
echo.
echo [4/5] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo .env file created from template
    echo.
    echo IMPORTANT: Edit .env file and add your OpenAI API key
    echo You can get an API key from: https://platform.openai.com/api-keys
) else (
    echo .env file already exists
)

REM Verify configuration
echo.
echo [5/5] Verifying configuration...
if exist config.yaml (
    echo config.yaml found
) else (
    echo WARNING: config.yaml not found
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env and add your OPENAI_API_KEY
echo 2. Run: venv\Scripts\activate
echo 3. Run: python src\main.py
echo.
echo For quick start guide, see QUICKSTART.md
echo For full documentation, see README.md
echo.
pause
